import json
from typing import Type, TypeVar, Any
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class LLMClient:
    """Mocked LLM Client for the Buildathon context where real keys might not be present."""
    
    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        # In a real app, this calls an LLM API (e.g. OpenAI/Gemini) with structured output
        # For this demo, we'll return a static mock that matches common queries
        
        # Super basic heuristic for demo purposes
        category = "headphones" if "headphone" in prompt.lower() else "laptop"
        budget = 500000 if "5000" in prompt else (6000000 if "60000" in prompt else 1000000)
        
        data = {
            "category": category,
            "max_budget": budget,
            "requirements": ["ANC"] if "anc" in prompt.lower() else [],
            "delivery_deadline_days": 3 if "3 days" in prompt.lower() else 5,
            "preferences": []
        }
        
        return schema(**data)

llm_client = LLMClient()
