# llm_clients/base.py

from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    async def audit(self, system_prompt, input_data, schema):
        pass
