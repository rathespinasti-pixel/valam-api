import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

class GeminiServiceError(Exception):
    """Custom exception raised when Gemini API call fails."""
    pass

class GeminiService:
    """Core low-level service for interacting with Google Gemini REST API."""

    @staticmethod
    def get_api_key():
        key = current_app.config.get("GEMINI_API_KEY") if current_app else None
        if not key:
            import os
            key = os.getenv("GEMINI_API_KEY") or os.getenv("GWMINI_API_KEY")
        if not key:
            raise GeminiServiceError("Gemini API key is not configured in backend environment.")
        return key

    @classmethod
    def generate_content(cls, prompt: str, system_instruction: str = None, temperature: float = 0.7, timeout: int = 15) -> str:
        """
        Sends a generation request to Gemini REST API securely from backend.
        """
        api_key = cls.get_api_key()
        model = current_app.config.get("GEMINI_MODEL", "gemini-1.5-flash") if current_app else "gemini-1.5-flash"
        
        # Primary endpoint and fallback models
        models_to_try = [model, "gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro"]
        # Deduplicate while maintaining order
        models_to_try = list(dict.fromkeys(models_to_try))

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        last_error = None

        for m in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}

            try:
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
                    raise GeminiServiceError("No text content returned from Gemini response.")
                else:
                    error_msg = response.text
                    try:
                        error_json = response.json()
                        error_msg = error_json.get("error", {}).get("message", response.text)
                    except Exception:
                        pass
                    last_error = f"Gemini API returned status {response.status_code}: {error_msg}"
                    logger.warning(f"Gemini model {m} failed: {last_error}")
            except requests.Timeout:
                last_error = f"Request to Gemini API model {m} timed out after {timeout} seconds."
                logger.warning(last_error)
            except requests.RequestException as req_err:
                last_error = f"Network error connecting to Gemini API: {str(req_err)}"
                logger.warning(last_error)

        raise GeminiServiceError(last_error or "Failed to receive valid response from Gemini API.")
