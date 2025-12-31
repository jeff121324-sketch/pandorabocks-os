"""
LLM Registry (Operational Layer)

This registry is responsible for routing requests to concrete LLM clients
based on role and runtime requirements.

IMPORTANT:
- This module is NOT part of governance.
- It MUST NOT make authoritative or irreversible decisions.
- Routing policies are operational and allowed to change between versions.
"""

from typing import Dict, Tuple, Type

from .base import BaseLLMClient
from .gpt import GPTClient
from .claude import ClaudeClient
from .gemini import GeminiClient
from .grok import GrokClient


class LLMRegistry:
    """
    Minimal, cache-based LLM client registry.

    Responsibility:
    - Given (role, requirement) -> return an LLM client instance

    Non-responsibility:
    - No governance logic
    - No voting or arbitration
    - No retry / fallback / safety policy
    """

    def __init__(self):
        # provider name -> client class
        self._providers: Dict[str, Type[BaseLLMClient]] = {
            "gpt": GPTClient,
            "claude": ClaudeClient,
            "gemini": GeminiClient,
            "grok": GrokClient,
        }

        # (provider, model) -> client instance
        self._pool: Dict[Tuple[str, str], BaseLLMClient] = {}

    def get(self, *, role: str, requirement: Dict) -> BaseLLMClient:
        """
        Get an LLM client based on role and requirement.

        Args:
            role: semantic role (e.g. auditor, writer, planner)
            requirement: runtime hints (latency, cost, accuracy, etc.)

        Returns:
            BaseLLMClient instance
        """
        provider, model = self._route(role, requirement)
        return self._get_or_create(provider, model)

    # ---------------------------------------------------------------------
    # Internal
    # ---------------------------------------------------------------------

    def _route(self, role: str, requirement: Dict) -> Tuple[str, str]:
        """
        Operational routing policy.

        This method is intentionally simple and replaceable.
        It MUST NOT encode governance or authority logic.
        """

        # Example baseline policy (v0.5)
        if role == "auditor":
            return "claude", "claude-3-haiku"

        if role == "writer":
            return "gpt", "gpt-4o-mini"

        if role == "planner":
            return "gpt", "gpt-4o"

        if role == "fast":
            return "gemini", "gemini-1.5-flash"

        # Default fallback (operational, not safety-related)
        return "gpt", "gpt-4o-mini"

    def _get_or_create(self, provider: str, model: str) -> BaseLLMClient:
        key = (provider, model)

        if key in self._pool:
            return self._pool[key]

        if provider not in self._providers:
            raise ValueError(f"Unknown LLM provider: {provider}")

        client_cls = self._providers[provider]
        client = client_cls(model=model)

        self._pool[key] = client
        return client
