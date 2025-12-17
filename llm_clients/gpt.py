import os
from .base import BaseLLMClient

class GPTClient(BaseLLMClient):
    """
    GPT Client (OpenAI)
    model: mini | full
    """

    def __init__(self, model: str):
        super().__init__(model)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not found in environment")

        self.api_key = api_key
        # self.client = OpenAI(api_key=api_key)

    async def audit(self, system_prompt, input_data, schema):
        if self.model == "mini":
            return await self._audit_mini(system_prompt, input_data, schema)
        return await self._audit_full(system_prompt, input_data, schema)

    async def _audit_mini(self, system_prompt, input_data, schema):
        return {
            "provider": "gpt",
            "model": "mini",
            "overall_status": "PASS",
            "confidence": 0.98
        }

    async def _audit_full(self, system_prompt, input_data, schema):
        return {
            "provider": "gpt",
            "model": "full",
            "overall_status": "PASS",
            "confidence": 0.995
        }
