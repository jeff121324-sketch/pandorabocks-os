import os
from .base import BaseLLMClient

class ClaudeClient(BaseLLMClient):
    """
    Claude Client
    model: mini | full
    """

    def __init__(self, model: str):
        super().__init__(model)

        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise RuntimeError("CLAUDE_API_KEY not found in environment")

        self.api_key = api_key
        # self.client = Anthropic(api_key=api_key)

    async def audit(self, system_prompt, input_data, schema):
        if self.model == "mini":
            return await self._audit_mini(system_prompt, input_data, schema)
        return await self._audit_full(system_prompt, input_data, schema)

    async def _audit_mini(self, system_prompt, input_data, schema):
        return {
            "provider": "claude",
            "model": "mini",
            "overall_status": "PASS",
            "confidence": 0.99
        }

    async def _audit_full(self, system_prompt, input_data, schema):
        return {
            "provider": "claude",
            "model": "full",
            "overall_status": "PASS",
            "confidence": 0.999
        }
