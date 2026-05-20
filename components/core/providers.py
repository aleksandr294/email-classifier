import abc

import pydantic


class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    async def classify(self, content: str) -> pydantic.BaseModel: ...
