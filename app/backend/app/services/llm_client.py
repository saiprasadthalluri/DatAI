"""LLM client wrapper for inference API."""
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from openai import AsyncOpenAI
from ..core.config import settings
from ..core.text_cleaner import clean_response

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Wrapper around OpenAI-compatible inference API.
    """

    def __init__(self):
        self._client = AsyncOpenAI(
            base_url=settings.inference_base_url,
            api_key=settings.inference_api_key,
        )
        self._model_registry = settings.model_registry

    def get_model_id(self, friendly_name: str) -> str:
        """Convert friendly name to model ID."""
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
        """
        actual_model_id = self.get_model_id(model_friendly_name)

        try:
            response = await self._client.chat.completions.create(
                model=actual_model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            raw_response = response.choices[0].message.content or ""
            cleaned_response = clean_response(raw_response)
            
            return {
                "model": model_friendly_name,
                "response": cleaned_response,
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

            in_thinking = False
            buffer = ""
            thinking_tags = ['<think>', '<thinking>', '<reasoning>', '<thought>', '<internal>']
            closing_tags = ['</think>', '</thinking>', '</reasoning>', '</thought>', '</internal>']
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    buffer += content
                    
                    for tag in thinking_tags:
                        if tag in buffer.lower():
                            in_thinking = True
                            tag_pos = buffer.lower().find(tag)
                            before_tag = buffer[:tag_pos]
                            if before_tag:
                                cleaned = self._clean_chunk(before_tag)
                                if cleaned:
                                    yield cleaned
                            buffer = buffer[tag_pos:]
                            break
                    
                    for tag in closing_tags:
                        if tag in buffer.lower():
                            in_thinking = False
                            tag_pos = buffer.lower().find(tag) + len(tag)
                            buffer = buffer[tag_pos:]
                            break
                    
                    if not in_thinking and buffer:
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
            
            if buffer and not in_thinking:
                cleaned = self._clean_chunk(buffer)
                if cleaned:
                    yield cleaned
                    
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            raise
    
    def _clean_chunk(self, content: str) -> str:
        """Clean a chunk of text."""
        cleaned = content.replace('**', '').replace('*', '').replace('#', '').replace('`', '').replace('__', '')
        return cleaned

    def get_available_models(self) -> List[str]:
        """Return list of available friendly model names."""
        return [k for k in self._model_registry.keys() if k != "safety-classifier"]


_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
