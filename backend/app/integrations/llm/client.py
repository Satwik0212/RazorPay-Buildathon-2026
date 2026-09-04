import httpx
import json
import logging
import re
from typing import Type, TypeVar, Any, Dict, List, Optional
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class GroqProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = settings.GROQ_MODEL

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None) -> Optional[T]:
        if not self.api_key:
            return None

        try:
            schema_json = schema.model_json_schema()

            if system_prompt is None:
                system_prompt = f"""You are a specialized buyer intent extraction engine.
You MUST output strictly valid JSON matching the following JSON schema:
{json.dumps(schema_json)}

Extract the user's intent. Do NOT add markdown formatting. Output raw JSON only."""
            else:
                system_prompt = f"""{system_prompt}

You MUST output strictly valid JSON matching the following JSON schema:
{json.dumps(schema_json)}

Do NOT add markdown formatting. Output raw JSON only."""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.0,
                "max_tokens": 1024
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()

            result_json = response.json()
            content = result_json["choices"][0]["message"]["content"]

            parsed_data = json.loads(content)
            return schema.model_validate(parsed_data)
        except Exception as e:
            # We don't log the API key or full exception string which might contain headers
            logger.warning("Groq API call failed")
            return None



    def generate_text(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        if not self.api_key:
            return None
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()

            result_json = response.json()
            return result_json["choices"][0]["message"]["content"]
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Groq text API call failed")
            return None

class SarvamProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sarvam.ai/v1/chat/completions"
        self.model = settings.SARVAM_MODEL

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None) -> Optional[T]:
        if not self.api_key:
            return None

        try:
            schema_json = schema.model_json_schema()

            if system_prompt is None:
                system_prompt = f"""Extract the user's intent as JSON matching this schema:
{json.dumps(schema_json)}

Respond with JSON only. No explanations."""
            else:
                system_prompt = f"""{system_prompt}

Output JSON matching this schema:
{json.dumps(schema_json)}

Respond with JSON only. No explanations."""

            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.0,
                "max_tokens": 1024
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()

            result_json = response.json()
            content = result_json["choices"][0]["message"]["content"]

            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            parsed_data = json.loads(content)
            return schema.model_validate(parsed_data)
        except Exception as e:
            logger.warning("Sarvam API call failed")
            return None



    def generate_text(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        if not self.api_key:
            return None
        try:
            import httpx
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()

            result_json = response.json()
            return result_json["choices"][0]["message"]["content"]
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Sarvam text API call failed")
            return None

class OfflineProvider:
    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        text = prompt.lower()
        categories = [
            "laptop", "notebook", "headphones", "earphones", "earbuds",
            "microphone", "mic", "smartphone", "phone", "mobile", "keyboard", "mouse",
            "monitor", "display", "smartwatch", "watch", "camera",
            "tablet", "speaker", "audio", "clothing", "shoes", "backpack",
            "electronics", "accessories"
        ]
        category = None
        for cat in categories:
            if re.search(r'\b' + re.escape(cat) + r'\b', text):
                if cat == "notebook":
                    category = "laptop"
                elif cat in ["earphones", "earbuds"]:
                    category = "headphones"
                elif cat == "mic":
                    category = "microphone"
                elif cat in ["smartphone", "mobile"]:
                    category = "phone"
                elif cat == "display":
                    category = "monitor"
                elif cat == "smartwatch":
                    category = "watch"
                else:
                    category = cat
                break

        max_budget = None
        min_budget = None
        max_match = re.search(
            r'(?:under|below|less than|max(?:imum)?(?: of)?|budget(?: of)?|upto|up to|around|approx(?:imately)?|about|for|near)\s*(?:rs\.?|inr|₹)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(k|thousand|lakh|lac|m|million)?',
            text
        )
        if max_match:
            val_str = max_match.group(1).replace(",", "")
            multiplier_str = (max_match.group(2) or "").lower()
            val = float(val_str)
            if multiplier_str in ["k", "thousand"]:
                val *= 1000
            elif multiplier_str in ["lakh", "lac"]:
                val *= 100000
            elif multiplier_str in ["m", "million"]:
                val *= 1000000
            max_budget = int(val * 100) if val < 1000000 else int(val)

        if max_budget is None:
            num_match = re.search(r'(?:rs\.?|inr|₹)\s*([0-9]+(?:,[0-9]+)*)', text)
            if num_match:
                val = float(num_match.group(1).replace(",", ""))
                max_budget = int(val * 100) if val < 1000000 else int(val)

        min_match = re.search(
            r'(?:above|more than|min(?:imum)?(?: of)?|at least)\s*(?:rs\.?|inr|₹)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(k|thousand|lakh|lac)?',
            text
        )
        if min_match:
            val_str = min_match.group(1).replace(",", "")
            multiplier_str = (min_match.group(2) or "").lower()
            val = float(val_str)
            if multiplier_str in ["k", "thousand"]:
                val *= 1000
            elif multiplier_str in ["lakh", "lac"]:
                val *= 100000
            min_budget = int(val * 100) if val < 1000000 else int(val)

        requirements = []
        feature_keywords = [
            ("anc", "ANC"), ("noise cancel", "ANC"), ("gaming", "gaming"),
            ("wireless", "wireless"), ("bluetooth", "bluetooth"),
            ("fast delivery", "fast_delivery"), ("express delivery", "fast_delivery"),
            ("waterproof", "waterproof"), ("16gb", "16GB_RAM"),
            ("32gb", "32GB_RAM"), ("rtx", "dedicated_gpu"),
            ("gpu", "dedicated_gpu"), ("ssd", "SSD"), ("oled", "OLED"),
            ("4k", "4K"), ("type-c", "type-c"), ("usb-c", "type-c"),
            ("mechanical", "mechanical"), ("leather", "leather"),
            ("in stock", "in_stock"), ("warranty", "warranty")
        ]
        for kw, req_name in feature_keywords:
            if kw in text and req_name not in requirements:
                requirements.append(req_name)

        delivery_deadline_days = None
        delivery_match = re.search(r'(?:within|in|under)\s*([0-9]+)\s*days?', text)
        if delivery_match:
            delivery_deadline_days = int(delivery_match.group(1))
        elif "next day" in text or "tomorrow" in text or "1 day" in text:
            delivery_deadline_days = 1
        elif "same day" in text or "today" in text:
            delivery_deadline_days = 0
        elif "fast delivery" in text or "quick delivery" in text or "express" in text:
            delivery_deadline_days = 2

        preferences = []
        pref_keywords = [
            ("high performance", "high_performance"), ("premium", "premium"),
            ("cheapest", "budget_friendly"), ("cheap", "budget_friendly"),
            ("budget", "budget_friendly"), ("lightweight", "lightweight"),
            ("durable", "durable"), ("good battery", "long_battery_life"),
            ("long battery", "long_battery_life"), ("battery life", "long_battery_life"),
            ("battery backup", "long_battery_life"), ("audio quality", "high_audio_quality"),
            ("sound quality", "high_audio_quality"), ("black", "color_black"),
            ("silver", "color_silver"), ("ergonomic", "ergonomic"),
            ("discount", "has_discount"), ("offer", "has_offer")
        ]
        for kw, pref_name in pref_keywords:
            if kw in text and pref_name not in preferences:
                preferences.append(pref_name)

        data = {
            "category": category,
            "min_budget": min_budget,
            "max_budget": max_budget,
            "requirements": requirements,
            "delivery_deadline_days": delivery_deadline_days,
            "preferences": preferences,
        }
        return schema(**data)



    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        return "Check out our latest offerings and upgrade your experience today."

class LLMClient:
    """
    LLM Client adapter with Groq (Primary), Sarvam (Fallback), and Offline (Emergency) routing.
    """
    def __init__(self):
        self.groq = GroqProvider(settings.GROQ_API_KEY)
        self.sarvam = SarvamProvider(settings.SARVAM_API_KEY)
        self.offline = OfflineProvider()

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None) -> T:
        # Try Groq
        if settings.GROQ_API_KEY:
            try:
                result = self.groq.generate_structured(prompt, schema, system_prompt)
                if result is not None:
                    logger.info("provider=groq")
                    return result
            except Exception:
                pass

        # Try Sarvam
        if settings.SARVAM_API_KEY:
            try:
                result = self.sarvam.generate_structured(prompt, schema, system_prompt)
                if result is not None:
                    logger.info("provider=sarvam")
                    return result
            except Exception:
                pass

        # Emergency Offline
        logger.info("provider=offline")
        return self.offline.generate_structured(prompt, schema)



    def generate_text(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        if settings.GROQ_API_KEY:
            try:
                result = self.groq.generate_text(prompt, system_prompt)
                if result is not None:
                    return result
            except Exception:
                pass

        if settings.SARVAM_API_KEY:
            try:
                result = self.sarvam.generate_text(prompt, system_prompt)
                if result is not None:
                    return result
            except Exception:
                pass

        return self.offline.generate_text(prompt, system_prompt)

llm_client = LLMClient()
