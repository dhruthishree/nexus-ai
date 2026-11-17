from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from app.core.config import settings

class LLMServiceBase(ABC):
    @abstractmethod
    def generate_response(
        self,
        system_instruction: str,
        user_prompt: str
    ) -> Tuple[str, int, int]:
        """
        Generates text given instructions and user prompt.
        Returns: (answer_text, input_tokens, output_tokens)
        """
        pass

def calculate_rag_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Computes exact API dollar cost based on model pricing configuration.
    """
    cost_in = (input_tokens / 1_000_000.0) * settings.COST_PER_1M_INPUT_TOKENS
    cost_out = (output_tokens / 1_000_000.0) * settings.COST_PER_1M_OUTPUT_TOKENS
    return round(cost_in + cost_out, 6)

