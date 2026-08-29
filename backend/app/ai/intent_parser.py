from app.schemas.buyer.intent import StructuredIntent, BuyerIntent
from app.integrations.llm.client import llm_client
from app.ai.prompt_safety import PromptSafety


class IntentParser:
    """
    Translates untrusted buyer natural language prompts into validated StructuredIntent.
    Protects against prompt injection and ensures deterministic Pydantic schema validation.
    """

    def parse(self, text: str) -> StructuredIntent:
        """
        Parses natural language into structured BuyerIntent.
        """
        sanitized = PromptSafety.sanitize_input(text)
        safe_prompt = PromptSafety.wrap_untrusted_content("untrusted_buyer_text", sanitized)

        return llm_client.generate_structured(safe_prompt, StructuredIntent)


intent_parser = IntentParser()
