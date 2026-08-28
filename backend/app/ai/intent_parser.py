from app.schemas.buyer.intent import BuyerIntent
from app.integrations.llm.client import llm_client

class IntentParser:
    def parse(self, text: str) -> BuyerIntent:
        """
        Parses natural language into structured BuyerIntent.
        """
        # Ensure we wrap the text clearly to avoid prompt injection (safety regulation)
        prompt = f"""
        Extract the buyer's intent from the following text.
        
        <untrusted_buyer_text>
        {text}
        </untrusted_buyer_text>
        """
        
        return llm_client.generate_structured(prompt, BuyerIntent)

intent_parser = IntentParser()
