"""Inference endpoints for specialist models."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel, Field
from ...api.v1.deps import current_user
from ...db.session import get_db
from ...models import User
from ...services.llm_client import get_llm_client
from ...services.safety import get_safety_service
from ...services.router import get_query_router

router = APIRouter(tags=["inference"])


class Message(BaseModel):
    """Message model."""
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class InferenceRequest(BaseModel):
    """Inference request."""
    model: str = Field(
        ...,
        description="Model to use: 'theory-specialist', 'code-specialist', 'math-specialist', or 'auto'"
    )
    messages: List[Message] = Field(..., description="Conversation messages")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1, le=8192)


class InferenceResponse(BaseModel):
    """Inference response."""
    model: str = Field(..., description="Model used (friendly name)")
    response: str = Field(..., description="Model response")
    usage: dict = Field(default_factory=dict, description="Token usage stats")


class ModelInfo(BaseModel):
    """Model information."""
    id: str
    description: str
    category: str


class ModelsResponse(BaseModel):
    """Models list response."""
    models: List[ModelInfo]


@router.post("/inference", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run inference on our specialist models.
    
    Available models:
    - theory-specialist: Explains complex data science concepts
    - code-specialist: Generates and explains code  
    - math-specialist: Solves mathematical problems
    
    Or use "auto" to automatically route based on query content.
    """
    llm_client = get_llm_client()
    safety_service = get_safety_service()
    query_router = get_query_router()
    
    # Validate model
    available_models = llm_client.get_available_models() + ["auto"]
    if request.model not in available_models:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{request.model}'. Available: {available_models}"
        )
    
    # Safety check on input
    safety_result = await safety_service.check_input(
        [m.model_dump() for m in request.messages]
    )
    if not safety_result["safe"]:
        raise HTTPException(
            status_code=400,
            detail=f"Input blocked: {safety_result.get('reason', 'Content flagged by safety classifier')}"
        )
    
    # Auto-route if requested
    model_to_use = request.model
    if request.model == "auto":
        latest_message = request.messages[-1].content if request.messages else ""
        model_to_use = query_router.classify(latest_message)
    
    # Run inference
    try:
        result = await llm_client.chat_completion(
            model_friendly_name=model_to_use,
            messages=[m.model_dump() for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
    
    # Safety check on output
    output_safety = await safety_service.check_output(result["response"])
    if not output_safety["safe"]:
        raise HTTPException(
            status_code=400,
            detail="Response blocked by safety filter"
        )
    
    return InferenceResponse(
        model=result["model"],
        response=result["response"],
        usage=result["usage"]
    )


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """List available specialist models."""
    return ModelsResponse(
        models=[
            ModelInfo(
                id="theory-specialist",
                description="Fine-tuned for explaining data science concepts, ML theory, and statistical methods",
                category="theory"
            ),
            ModelInfo(
                id="code-specialist",
                description="Fine-tuned for code generation, debugging, and programming explanations",
                category="code"
            ),
            ModelInfo(
                id="math-specialist",
                description="Fine-tuned for mathematical problem solving and statistical computations",
                category="math"
            ),
            ModelInfo(
                id="auto",
                description="Automatically routes to the best specialist based on query content",
                category="router"
            ),
        ]
    )

