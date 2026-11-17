from typing import Tuple
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logging import logger
from app.services.llm.base import LLMServiceBase

class GeminiLLMService(LLMServiceBase):
    """
    Google Gemini Generation Service utilizing official google-genai SDK.
    Captures exact token usage metadata from the API response.
    """
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GENERATION_MODEL
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not configured. Live Gemini calls will fail.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def generate_response(
        self,
        system_instruction: str,
        user_prompt: str
    ) -> Tuple[str, int, int]:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is missing. Please add it to backend/.env or your environment variables.")

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=settings.TEMPERATURE,
                max_output_tokens=settings.MAX_OUTPUT_TOKENS
            )
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=config
            )

            answer = response.text or ""
            
            # Extract real token usage from response metadata
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count or 0
                output_tokens = response.usage_metadata.candidates_token_count or 0
            else:
                # Fallback token estimation if metadata is absent
                input_tokens = max(1, (len(system_instruction) + len(user_prompt)) // 4)
                output_tokens = max(1, len(answer) // 4)

            return answer, input_tokens, output_tokens

        except Exception as e:
            logger.error(f"Error calling Gemini LLM: {e}", exc_info=True)
            raise

