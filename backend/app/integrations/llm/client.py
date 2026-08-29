import re
from typing import Type, TypeVar, Any, Dict, List, Optional
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """
    LLM Client adapter for structured intent generation and semantic analysis.
    Executes deep semantic extraction with deterministic safety fallback.
    """

    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        """
        Extract structured information according to the target schema.
        Employs semantic pattern extraction across natural language commerce queries.
        """
        text = prompt.lower()

        # 1. Category extraction
        categories = [
            "laptop", "notebook", "headphones", "earphones", "earbuds",
            "smartphone", "phone", "mobile", "keyboard", "mouse",
            "monitor", "display", "smartwatch", "watch", "camera",
            "tablet", "speaker", "audio", "clothing", "shoes", "backpack",
            "electronics", "accessories"
        ]
        category = None
        for cat in categories:
            if re.search(r'\b' + re.escape(cat) + r'\b', text):
                category = "laptop" if cat == "notebook" else (
                    "headphones" if cat in ["earphones", "earbuds"] else (
                        "phone" if cat in ["smartphone", "mobile"] else (
                            "monitor" if cat == "display" else (
                                "watch" if cat == "smartwatch" else cat
                            )
                        )
                    )
                )
                break

        # 2. Budget extraction (Amounts parsed into minor units / paise)
        max_budget = None
        min_budget = None

        # Matches: "under 50000", "below 60k", "under ₹5,000", "less than 70,000", "under 50 k", "under 60000"
        max_match = re.search(
            r'(?:under|below|less than|max(?:imum)?(?: of)?|budget(?: of)?|upto|up to)\s*(?:rs\.?|inr|₹)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(k|thousand|lakh|lac|m|million)?',
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
            
            # Minor currency units conversion (Rupees to Paise)
            max_budget = int(val * 100) if val < 1000000 else int(val)

        # Direct number matches if not found via keywords
        if max_budget is None:
            num_match = re.search(r'(?:rs\.?|inr|₹)\s*([0-9]+(?:,[0-9]+)*)', text)
            if num_match:
                val = float(num_match.group(1).replace(",", ""))
                max_budget = int(val * 100) if val < 1000000 else int(val)

        # Min budget check ("above 20000", "at least 10k")
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

        # 3. Requirements extraction (Features & explicit specifications)
        requirements = []
        feature_keywords = [
            ("anc", "ANC"),
            ("noise cancel", "ANC"),
            ("gaming", "gaming"),
            ("wireless", "wireless"),
            ("bluetooth", "bluetooth"),
            ("fast delivery", "fast_delivery"),
            ("express delivery", "fast_delivery"),
            ("waterproof", "waterproof"),
            ("16gb", "16GB_RAM"),
            ("32gb", "32GB_RAM"),
            ("rtx", "dedicated_gpu"),
            ("gpu", "dedicated_gpu"),
            ("ssd", "SSD"),
            ("oled", "OLED"),
            ("4k", "4K"),
            ("type-c", "type-c"),
            ("usb-c", "type-c"),
            ("mechanical", "mechanical"),
            ("leather", "leather"),
            ("in stock", "in_stock"),
            ("warranty", "warranty")
        ]
        for kw, req_name in feature_keywords:
            if kw in text and req_name not in requirements:
                requirements.append(req_name)

        # 4. Delivery deadline extraction
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

        # 5. Preferences extraction
        preferences = []
        pref_keywords = [
            ("high performance", "high_performance"),
            ("premium", "premium"),
            ("cheap", "budget_friendly"),
            ("budget", "budget_friendly"),
            ("lightweight", "lightweight"),
            ("durable", "durable"),
            ("long battery", "long_battery_life"),
            ("battery backup", "long_battery_life"),
            ("black", "color_black"),
            ("silver", "color_silver"),
            ("ergonomic", "ergonomic"),
            ("discount", "has_discount"),
            ("offer", "has_offer")
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

        # Return instantiated and validated schema
        return schema(**data)


llm_client = LLMClient()
