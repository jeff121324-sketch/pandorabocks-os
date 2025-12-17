import os
from .base import BaseLLMClient

class GeminiClient(BaseLLMClient):
    """
    Gemini Client (Google)
    model: mini | full
    """

    def __init__(self, model: str):
        super().__init__(model)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not found in environment")

        self.api_key = api_key
        # self.client = genai.Client(api_key=api_key)

    async def audit(self, system_prompt, input_data, schema):
        if self.model == "mini":
            return await self._audit_mini(system_prompt, input_data, schema)
        return await self._audit_full(system_prompt, input_data, schema)

    async def _audit_mini(self, system_prompt, input_data, schema):
        # 適合快速掃描 / 防禦 / 監控
        return {
            "provider": "gemini",
            "model": "mini",
            "overall_status": "PASS",
            "confidence": 0.97
        }

    async def _audit_full(self, system_prompt, input_data, schema):
        # 適合中度推理 / 結構理解
        return {
            "provider": "gemini",
            "model": "full",
            "overall_status": "PASS",
            "confidence": 0.993
        }
