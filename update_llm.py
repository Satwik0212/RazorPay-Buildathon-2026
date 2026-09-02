import re

with open("backend/app/integrations/llm/client.py", "r") as f:
    text = f.read()

groq_method = """
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
"""

sarvam_method = """
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
"""

offline_method = """
    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        return "Special Offer! 10% discount on selected products. Upgrade your experience today."
"""

llm_client_method = """
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
"""

text = text.replace('class SarvamProvider:', groq_method + '\nclass SarvamProvider:')
text = text.replace('class OfflineProvider:', sarvam_method + '\nclass OfflineProvider:')
text = text.replace('class LLMClient:', offline_method + '\nclass LLMClient:')
text = text.replace('llm_client = LLMClient()', llm_client_method + '\nllm_client = LLMClient()')

with open("backend/app/integrations/llm/client.py", "w") as f:
    f.write(text)
