"""LLM client wrapper - hides actual model details and API endpoints."""
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from openai import AsyncOpenAI
from ..core.config import settings
from ..core.text_cleaner import clean_response

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Wrapper around OpenAI-compatible API (OpenRouter).
    Hides the actual provider and model details.
    """

    def __init__(self):
        # Use hidden API configuration
        self._client = AsyncOpenAI(
            base_url=settings.inference_base_url,  # From hidden config
            api_key=settings.inference_api_key,  # From hidden config
        )
        self._model_registry = settings.model_registry  # Maps to hidden models

    def get_model_id(self, friendly_name: str) -> str:
        """Convert friendly name to actual model ID."""
        if friendly_name not in self._model_registry:
            raise ValueError(f"Unknown model: {friendly_name}")
        return self._model_registry[friendly_name]

    async def chat_completion(
        self,
        model_friendly_name: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Run chat completion using friendly model name.
        Returns response with friendly name (not actual model ID).
        """
        actual_model_id = self.get_model_id(model_friendly_name)

        try:
            response = await self._client.chat.completions.create(
                model=actual_model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Clean response: remove thinking/reasoning and markdown
            raw_response = response.choices[0].message.content or ""
            cleaned_response = clean_response(raw_response)
            
            return {
                "model": model_friendly_name,  # Return friendly name!
                "response": cleaned_response,  # Cleaned response without markdown
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            }
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise

    async def chat_completion_stream(
        self,
        model_friendly_name: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion using friendly model name.
        Yields chunks of the response text.
        Filters out thinking/reasoning tags in real-time.
        """
        actual_model_id = self.get_model_id(model_friendly_name)

        try:
            stream = await self._client.chat.completions.create(
                model=actual_model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # State for tracking thinking tags
            in_thinking = False
            buffer = ""
            thinking_tags = ['<think>', '<thinking>', '<reasoning>', '<thought>', '<internal>']
            closing_tags = ['</think>', '</thinking>', '</reasoning>', '</thought>', '</internal>']
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    buffer += content
                    
                    # Check for thinking tag starts
                    for tag in thinking_tags:
                        if tag in buffer.lower():
                            in_thinking = True
                            # Remove everything from start of tag
                            tag_pos = buffer.lower().find(tag)
                            # Yield content before the tag
                            before_tag = buffer[:tag_pos]
                            if before_tag:
                                cleaned = self._clean_chunk(before_tag)
                                if cleaned:
                                    yield cleaned
                            buffer = buffer[tag_pos:]
                            break
                    
                    # Check for thinking tag ends
                    for tag in closing_tags:
                        if tag in buffer.lower():
                            in_thinking = False
                            # Skip everything up to and including closing tag
                            tag_pos = buffer.lower().find(tag) + len(tag)
                            buffer = buffer[tag_pos:]
                            break
                    
                    # If not in thinking, yield buffered content
                    if not in_thinking and buffer:
                        # Only yield if we don't have partial tags
                        has_partial_tag = any(
                            buffer.lower().endswith(tag[:i]) 
                            for tag in thinking_tags + closing_tags 
                            for i in range(1, len(tag))
                        )
                        if not has_partial_tag:
                            cleaned = self._clean_chunk(buffer)
                            if cleaned:
                                yield cleaned
                            buffer = ""
            
            # Yield any remaining buffer (if not in thinking)
            if buffer and not in_thinking:
                cleaned = self._clean_chunk(buffer)
                if cleaned:
                    yield cleaned
                    
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            raise
    
    def _clean_chunk(self, content: str) -> str:
        """Clean a chunk of text - remove markdown characters."""
        # Remove common markdown characters
        cleaned = content.replace('**', '').replace('*', '').replace('#', '').replace('`', '').replace('__', '')
        return cleaned

    def get_available_models(self) -> List[str]:
        """Return list of available friendly model names."""
        return [k for k in self._model_registry.keys() if k != "safety-classifier"]


# Singleton instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client

