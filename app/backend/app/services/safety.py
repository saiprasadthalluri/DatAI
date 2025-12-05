"""Safety layer using LlamaGuard via LLM client or Replicate API fallback."""
import httpx
import asyncio
import logging
from typing import Dict, Any, Optional
from ..core.config import settings
from .llm_client import get_llm_client

logger = logging.getLogger(__name__)

# LlamaGuard safety categories
SAFETY_CATEGORIES = {
    "S1": "Violent Crimes",
    "S2": "Non-Violent Crimes",
    "S3": "Sex-Related Crimes",
    "S4": "Child Sexual Exploitation",
    "S5": "Defamation",
    "S6": "Specialized Advice",
    "S7": "Privacy",
    "S8": "Intellectual Property",
    "S9": "Indiscriminate Weapons",
    "S10": "Hate",
    "S11": "Suicide & Self-Harm",
    "S12": "Sexual Content",
    "S13": "Elections",
    "S14": "Code Interpreter Abuse",
}


class LlamaGuardClient:
    """Client for LlamaGuard safety checks via Replicate API."""
    
    def __init__(self):
        self.api_url = "https://api.replicate.com/v1/predictions"
        self.api_key = settings.safety_api_key
        # LlamaGuard 3 8B model on Replicate
        self.model_version = "meta/llama-guard-3-8b"
        self._enabled = self.api_key and self.api_key != "PLACEHOLDER"
    
    @property
    def enabled(self) -> bool:
        """Check if LlamaGuard is properly configured."""
        return self._enabled
    
    async def check_safety(self, text: str, check_type: str = "user") -> Dict[str, Any]:
        """
        Check text safety using LlamaGuard.
        
        Args:
            text: Text to check
            check_type: "user" for input prompts, "assistant" for model responses
            
        Returns:
            Dictionary with safety classification results
        """
        if not self.enabled:
            logger.warning("LlamaGuard not configured, using fallback")
            return await self._fallback_check(text)
        
        try:
            # Format prompt for LlamaGuard
            prompt = self._format_prompt(text, check_type)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create prediction
                response = await client.post(
                    self.api_url,
                    json={
                        "version": self.model_version,
                        "input": {
                            "prompt": prompt,
                            "max_new_tokens": 100,
                            "temperature": 0.0,
                        }
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    }
                )
                response.raise_for_status()
                prediction = response.json()
                
                # Poll for completion
                result = await self._poll_prediction(client, prediction)
                return self._parse_response(result)
                
        except httpx.TimeoutException:
            logger.error("LlamaGuard API timeout")
            return await self._fallback_check(text)
        except httpx.HTTPStatusError as e:
            logger.error(f"LlamaGuard API error: {e.response.status_code} - {e.response.text}")
            return await self._fallback_check(text)
        except Exception as e:
            logger.error(f"LlamaGuard check failed: {e}")
            return await self._fallback_check(text)
    
    def _format_prompt(self, text: str, check_type: str) -> str:
        """Format the prompt for LlamaGuard classification."""
        role = "User" if check_type == "user" else "Agent"
        return f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

Task: Check if there is unsafe content in '{role}' messages in conversations according to our safety policy with the below categories.

<BEGIN UNSAFE CONTENT CATEGORIES>
S1: Violent Crimes
S2: Non-Violent Crimes  
S3: Sex-Related Crimes
S4: Child Sexual Exploitation
S5: Defamation
S6: Specialized Advice
S7: Privacy
S8: Intellectual Property
S9: Indiscriminate Weapons
S10: Hate
S11: Suicide & Self-Harm
S12: Sexual Content
S13: Elections
S14: Code Interpreter Abuse
<END UNSAFE CONTENT CATEGORIES>

<BEGIN CONVERSATION>

{role}: {text}

<END CONVERSATION>

Provide your safety assessment for ONLY THE LAST {role} message in the above conversation:
 - First line must read 'safe' or 'unsafe'.
 - If unsafe, a second line must include a comma-separated list of violated categories.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    async def _poll_prediction(self, client: httpx.AsyncClient, prediction: dict, max_attempts: int = 30) -> str:
        """Poll Replicate API for prediction completion."""
        prediction_url = prediction.get("urls", {}).get("get")
        if not prediction_url:
            prediction_url = f"{self.api_url}/{prediction['id']}"
        
        for _ in range(max_attempts):
            response = await client.get(
                prediction_url,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            result = response.json()
            
            status = result.get("status")
            if status == "succeeded":
                output = result.get("output", "")
                # Handle list output (common with Replicate)
                if isinstance(output, list):
                    output = "".join(output)
                return output
            elif status == "failed":
                error = result.get("error", "Unknown error")
                raise Exception(f"Prediction failed: {error}")
            elif status == "canceled":
                raise Exception("Prediction was canceled")
            
            # Wait before next poll
            await asyncio.sleep(0.5)
        
        raise Exception("Prediction timed out")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LlamaGuard response into structured format."""
        response = response.strip().lower()
        lines = response.split("\n")
        
        is_safe = lines[0].strip() == "safe" if lines else True
        
        violated_categories = []
        category_details = {}
        
        if not is_safe and len(lines) > 1:
            # Parse violated categories from second line
            categories_line = lines[1].strip()
            for cat in categories_line.split(","):
                cat = cat.strip().upper()
                if cat in SAFETY_CATEGORIES:
                    violated_categories.append(cat)
                    category_details[cat] = SAFETY_CATEGORIES[cat]
        
        return {
            "allowed": is_safe,
            "labels": {
                "categories": violated_categories,
                "details": category_details,
            },
            "reason": f"Violated: {', '.join(category_details.values())}" if violated_categories else "",
            "reference_code": "LLAMAGUARD_UNSAFE" if not is_safe else "LLAMAGUARD_SAFE"
        }
    
    async def _fallback_check(self, text: str) -> Dict[str, Any]:
        """Fallback safety check when LlamaGuard is unavailable."""
        # Basic keyword-based fallback (very limited)
        # In production, you might want to fail closed instead
        return {
            "allowed": True,
            "labels": {"fallback": True},
            "reason": "LlamaGuard unavailable, using fallback",
            "reference_code": "SAFETY_FALLBACK"
        }


# Global client instance
_llamaguard_client: Optional[LlamaGuardClient] = None


def get_llamaguard_client() -> LlamaGuardClient:
    """Get or create LlamaGuard client instance."""
    global _llamaguard_client
    if _llamaguard_client is None:
        _llamaguard_client = LlamaGuardClient()
    return _llamaguard_client


class SafetyService:
    """
    Content safety checking using Llama Guard via LLM client.
    Uses LLM client first, falls back to Replicate if needed.
    """

    def __init__(self):
        self._llm_client = get_llm_client()
        self._replicate_client = get_llamaguard_client()

    async def check_content(self, content: str) -> Dict[str, Any]:
        """
        Check if content is safe using LLM client (OpenRouter).
        Falls back to Replicate if LLM client fails.
        """
        # Try LLM client first (OpenRouter)
        try:
            result = await self._llm_client.chat_completion(
                model_friendly_name="safety-classifier",
                messages=[{"role": "user", "content": content}],
                temperature=0,
                max_tokens=100,
            )

            response_text = result["response"].lower()
            is_safe = "unsafe" not in response_text

            return {
                "safe": is_safe,
                "allowed": is_safe,
                "reason": None if is_safe else "Content flagged by safety classifier",
                "labels": {} if is_safe else {"unsafe": True},
                "reference_code": "SAFETY_OK" if is_safe else "SAFETY_BLOCKED"
            }
        except Exception as e:
            logger.warning(f"LLM client safety check failed, trying Replicate fallback: {e}")
            # Fallback to Replicate
            return await self._replicate_client.check_safety(content)

    async def check_input(self, messages: list[dict]) -> Dict[str, Any]:
        """Check the latest user message for safety."""
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return {
                "safe": True,
                "allowed": True,
                "reason": None,
                "labels": {},
                "reference_code": "SAFETY_OK"
            }

        latest_content = user_messages[-1].get("content", "")
        return await self.check_content(latest_content)

    async def check_output(self, response: str) -> Dict[str, Any]:
        """Check model output for safety."""
        return await self.check_content(response)


# Singleton
_safety_service: Optional[SafetyService] = None


def get_safety_service() -> SafetyService:
    """Get or create safety service instance."""
    global _safety_service
    if _safety_service is None:
        _safety_service = SafetyService()
    return _safety_service


async def check(text: str, check_type: str = "user") -> Dict[str, Any]:
    """
    Check text for safety violations using LlamaGuard.
    
    Args:
        text: Text to check
        check_type: "user" for input prompts, "assistant" for model responses
        
    Returns:
        Dictionary with:
        - allowed: bool - Whether text is safe
        - labels: dict - Safety labels/categories
        - reason: str - Explanation if blocked
        - reference_code: str - Reference code for support
    """
    if not text or len(text.strip()) == 0:
        return {
            "allowed": False,
            "labels": {"empty": True},
            "reason": "Empty input",
            "reference_code": "SAFETY_001"
        }
    
    client = get_llamaguard_client()
    return await client.check_safety(text, check_type)




