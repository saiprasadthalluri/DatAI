"""Chat endpoints."""
import time
import json
import asyncio
import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ...api.v1.deps import current_user
from ...db.session import get_db
from ...schemas.chat import ChatRequest, ChatResponse, RouterInfo, SafetyInfo
from ...models import User, MessageRole
from ...services import safety
from ...services.router import decide as router_decide
from ...services.llm_client import get_llm_client
from ...services.history import (
    get_conversation,
    create_conversation,
    save_message,
    save_router_decision
)
from ...core.rate_limit import get_rate_limiter
from ...core.config import settings
from ...core.text_cleaner import clean_response

router = APIRouter(prefix="/chat", tags=["chat"])


# Model name mapping for user-facing responses
MODEL_DISPLAY_NAMES = {
    "theory-specialist": "DatAI",
    "math-specialist": "DatAI", 
    "code-specialist": "DatAI",
    "auto": "DatAI",
}


def is_model_inquiry(message: str) -> bool:
    """Check if the user is asking about the model being used."""
    msg_lower = message.lower().strip()
    
    # Patterns that indicate asking about the model
    model_inquiry_patterns = [
        r"what.*model",
        r"which.*model",
        r"what.*are.*you",
        r"who.*are.*you",
        r"what.*is.*this.*model",
        r"what.*ai.*are.*you",
        r"what.*llm",
        r"which.*llm",
        r"what.*version",
        r"your.*name",
        r"identify.*yourself",
        r"what.*assistant",
    ]
    
    for pattern in model_inquiry_patterns:
        if re.search(pattern, msg_lower):
            return True
    
    return False


def get_model_identity_response(model_used: str, selected_model: str) -> str:
    """Generate a response identifying the model being used."""
    # Use the selected model from request meta, or the routed model
    display_name = MODEL_DISPLAY_NAMES.get(selected_model, MODEL_DISPLAY_NAMES.get(model_used, "DatAI"))
    
    return f"I am {display_name}, an AI assistant here to help you with your questions. How can I assist you today?"


@router.post("/send", response_model=ChatResponse)
async def send_chat(
    request: Request,
    req: ChatRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a chat message and get assistant response.
    
    Flow:
    1. Verify Firebase token (via current_user dependency)
    2. Safety-In: Check user prompt
    3. Router: Decide which endpoint/strategy to use
    4. Call model or fallback interpreter
    5. Safety-Out: Check model response
    6. Persist messages and router decision
    """
    start_time = time.time()
    
    # Rate limiting
    limiter = get_rate_limiter(settings.redis_url)
    client_ip = request.client.host if request.client else "unknown"
    
    # Check IP-based limit
    ip_allowed, ip_remaining = await limiter.check_rate_limit(
        f"rate_limit:ip:{client_ip}",
        settings.rate_limit_per_ip
    )
    if not ip_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded (IP-based)",
            headers={"X-RateLimit-Remaining": "0"}
        )
    
    # Check user-based limit
    user_allowed, user_remaining = await limiter.check_rate_limit(
        f"rate_limit:user:{user.id}",
        settings.rate_limit_per_user
    )
    if not user_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded (user-based)",
            headers={"X-RateLimit-Remaining": "0"}
        )
    
    # Safety-In: Check user prompt
    safety_in = await safety.check(req.message)
    if not safety_in.get("allowed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "safety": safety_in,
                "message": "Input flagged by safety policy"
            }
        )
    
    # Router: Decide which specialist model to use
    router_decision = await router_decide(req.meta.model_dump(), req.message)
    
    # Get or create conversation
    conversation_id = req.conversation_id
    if not conversation_id:
        # Generate title from first message (first 50 chars)
        title = req.message[:50].strip()
        if len(req.message) > 50:
            title = title.rsplit(' ', 1)[0] + '...'  # Don't cut mid-word
        conversation = await create_conversation(db, user.id, title=title)
        conversation_id = conversation.id
    else:
        conversation = await get_conversation(db, conversation_id, user.id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    
    # Save user message
    user_message = await save_message(
        db=db,
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=req.message,
        safety_labels=safety_in.get("labels")
    )
    
    # Call LLM
    model_used = router_decision.get("model", "theory-specialist")
    selected_model = req.meta.model or "auto"  # What user selected in UI
    
    # Check if user is asking about the model identity
    if is_model_inquiry(req.message):
        answer = get_model_identity_response(model_used, selected_model)
    else:
        llm_client = get_llm_client()
        
        # Build messages list (include conversation history if available)
        messages = [{"role": "user", "content": req.message}]
        
        # Get conversation history for context
        from ...services.history import get_conversation_messages
        history = await get_conversation_messages(db, conversation_id, limit=10)
        if history:
            # Build message history (skip the last one which is the current user message)
            messages = []
            for msg in history[:-1]:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            messages.append({"role": "user", "content": req.message})
        
        result = await llm_client.chat_completion(
            model_friendly_name=model_used,
            messages=messages,
            temperature=req.meta.temperature,
            max_tokens=req.meta.max_tokens
        )
        answer = result["response"]
    
    # Safety-Out: Check model response
    safety_out = await safety.check(answer)
    if not safety_out.get("allowed"):
        answer = "[This response was redacted by safety policy.]"
    
    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Save assistant message
    assistant_message = await save_message(
        db=db,
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=answer,
        tokens_in=None,  # TODO: Extract from model response
        tokens_out=None,  # TODO: Extract from model response
        latency_ms=latency_ms,
        safety_labels=safety_out.get("labels")
    )
    
    # Save router decision
    await save_router_decision(
        db=db,
        message_id=assistant_message.id,
        strategy="moe",  # Keep for compatibility
        selected_endpoint=model_used,
        confidence=router_decision.get("confidence"),
        reasons=router_decision.get("reasons")
    )
    
    return ChatResponse(
        assistant_message=answer,
        conversation_id=conversation_id,
        message_id=assistant_message.id,
        router=RouterInfo(
            strategy="moe",
            endpoint=model_used,
            confidence=router_decision.get("confidence", 0.5)
        ),
        safety=SafetyInfo(
            input=safety_in,
            output=safety_out
        )
    )


@router.post("/send-stream")
async def send_chat_stream(
    request: Request,
    req: ChatRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream chat response using Server-Sent Events (SSE).
    
    Returns streaming response with chunks of the assistant message.
    """
    start_time = time.time()
    
    # Rate limiting
    limiter = get_rate_limiter(settings.redis_url)
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limits
    ip_allowed, _ = await limiter.check_rate_limit(
        f"rate_limit:ip:{client_ip}",
        settings.rate_limit_per_ip
    )
    if not ip_allowed:
        async def error_stream():
            yield f"data: {json.dumps({'error': 'Rate limit exceeded', 'type': 'rate_limit'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    user_allowed, _ = await limiter.check_rate_limit(
        f"rate_limit:user:{user.id}",
        settings.rate_limit_per_user
    )
    if not user_allowed:
        async def error_stream():
            yield f"data: {json.dumps({'error': 'Rate limit exceeded', 'type': 'rate_limit'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    # Safety-In: Check user prompt
    safety_in = await safety.check(req.message)
    if not safety_in.get("allowed"):
        async def error_stream():
            yield f"data: {json.dumps({'error': 'Input flagged by safety policy', 'type': 'safety', 'safety': safety_in})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    # Router: Decide which specialist model to use
    router_decision = await router_decide(req.meta.model_dump(), req.message)
    
    # Get or create conversation
    conversation_id = req.conversation_id
    if not conversation_id:
        # Generate title from first message (first 50 chars)
        title = req.message[:50].strip()
        if len(req.message) > 50:
            title = title.rsplit(' ', 1)[0] + '...'  # Don't cut mid-word
        conversation = await create_conversation(db, user.id, title=title)
        conversation_id = conversation.id
    else:
        conversation = await get_conversation(db, conversation_id, user.id)
        if not conversation:
            async def error_stream():
                yield f"data: {json.dumps({'error': 'Conversation not found', 'type': 'not_found'})}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    # Save user message
    user_message = await save_message(
        db=db,
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=req.message,
        safety_labels=safety_in.get("labels")
    )
    
    async def generate_stream():
        """Generate streaming response."""
        full_answer = ""
        model_used = router_decision.get("model", "theory-specialist")
        selected_model = req.meta.model or "auto"  # What user selected in UI
        llm_client = get_llm_client()
        
        try:
            # Send initial metadata
            yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': str(conversation_id), 'message_id': str(user_message.id), 'model': model_used})}\n\n"
            
            # Check if user is asking about the model identity
            if is_model_inquiry(req.message):
                full_answer = get_model_identity_response(model_used, selected_model)
                # Stream the response word by word for consistency
                words = full_answer.split()
                for word in words:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': word + ' '})}\n\n"
                    await asyncio.sleep(0.02)  # Small delay for natural feel
            else:
                # Call LLM with streaming
                # Build messages list
                messages = [{"role": "user", "content": req.message}]
                
                # Get conversation history for context
                from ...services.history import get_conversation_messages
                history = await get_conversation_messages(db, conversation_id, limit=10)
                if history:
                    messages = []
                    for msg in history[:-1]:
                        messages.append({
                            "role": msg.role.value,
                            "content": msg.content
                        })
                    messages.append({"role": "user", "content": req.message})
                
                async for chunk in llm_client.chat_completion_stream(
                    model_friendly_name=model_used,
                    messages=messages,
                    temperature=req.meta.temperature,
                    max_tokens=req.meta.max_tokens
                ):
                    full_answer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            # Clean response: remove thinking/reasoning and markdown
            full_answer = clean_response(full_answer)
            
            # Safety-Out: Check model response
            safety_out = await safety.check(full_answer)
            if not safety_out.get("allowed"):
                full_answer = "[This response was redacted by safety policy.]"
                yield f"data: {json.dumps({'type': 'safety_redacted'})}\n\n"
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Save assistant message
            assistant_message = await save_message(
                db=db,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=full_answer,
                tokens_in=None,
                tokens_out=None,
                latency_ms=latency_ms,
                safety_labels=safety_out.get("labels")
            )
            
            # Save router decision
            await save_router_decision(
                db=db,
                message_id=assistant_message.id,
                strategy="moe",  # Keep for compatibility
                selected_endpoint=model_used,
                confidence=router_decision.get("confidence"),
                reasons=router_decision.get("reasons")
            )
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_message.id)})}\n\n"
            
        except Exception as e:
            # Send error
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.post("/simple")
async def simple_chat(
    request: Request,
    req: ChatRequest,
    user = Depends(current_user),
):
    """
    Simple stateless chat endpoint - no database required.
    For demo/testing purposes when database is not available.
    """
    # Router: Decide which specialist model to use
    router_decision = await router_decide(req.meta.model_dump(), req.message)
    model_used = router_decision.get("model", "theory-specialist")
    selected_model = req.meta.model or "auto"
    
    # Check if user is asking about the model identity
    if is_model_inquiry(req.message):
        answer = get_model_identity_response(model_used, selected_model)
    else:
        # Call LLM
        llm_client = get_llm_client()
        messages = [{"role": "user", "content": req.message}]
        
        result = await llm_client.chat_completion(
            model_friendly_name=model_used,
            messages=messages,
            temperature=req.meta.temperature,
            max_tokens=req.meta.max_tokens
        )
        answer = result["response"]
    
    return {
        "assistant_message": answer,
        "model": model_used,
        "confidence": router_decision.get("confidence", 0.5)
    }


@router.post("/simple-stream")
async def simple_chat_stream(
    request: Request,
    req: ChatRequest,
    user = Depends(current_user),
):
    """
    Simple stateless streaming chat - no database required.
    """
    router_decision = await router_decide(req.meta.model_dump(), req.message)
    model_used = router_decision.get("model", "theory-specialist")
    selected_model = req.meta.model or "auto"
    
    async def generate():
        yield f"data: {json.dumps({'type': 'metadata', 'model': model_used})}\n\n"
        
        if is_model_inquiry(req.message):
            answer = get_model_identity_response(model_used, selected_model)
            for word in answer.split():
                yield f"data: {json.dumps({'type': 'chunk', 'content': word + ' '})}\n\n"
                await asyncio.sleep(0.02)
        else:
            llm_client = get_llm_client()
            messages = [{"role": "user", "content": req.message}]
            
            async for chunk in llm_client.chat_completion_stream(
                model_friendly_name=model_used,
                messages=messages,
                temperature=req.meta.temperature,
                max_tokens=req.meta.max_tokens
            ):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

