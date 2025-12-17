from llm_clients.claude import ClaudeClient
from llm_clients.gpt import GPTClient
from llm_clients.gemini import GeminiClient
from llm_clients.grok import GrokClient

class LLMRegistry:
    def __init__(self):
        self._pool = {}

    def get(self, *, role: str, requirement: dict):
        """
        根據角色 + 需求，回傳一個 LLM client
        """

        key = (role, tuple(sorted(requirement.items())))

        if key in self._pool:
            return self._pool[key]

        # === 分發策略（你可以慢慢調） ===
        provider, model = self._route(role, requirement)

        if provider == "claude":
            client = ClaudeClient(model=model)
        elif provider == "gpt":
            client = GPTClient(model=model)
        elif provider == "gemini":
            client = GeminiClient(model=model)
        elif provider == "grok":
            client = GrokClient(model=model)
        else:
            raise ValueError("Unknown provider")

        self._pool[key] = client
        return client

    def _route(self, role, req):
        """
        核心分發邏輯（策略層）
        """

        # 🛡️ 感知稽核：快、便宜、保守
        if role == "auditor":
            return "claude", "mini"

        # 🧠 交易決策：深度推理
        if role == "trader":
            return "claude", "full"

        # 📣 解釋 / 對話
        if role == "advisor":
            return "gpt", "full"

        # 🧯 防禦 / 監控
        if role == "defender":
            return "gemini", "mini"

        # fallback
        return "claude", "mini"
