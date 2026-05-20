import anthropic

from components.core.config import get_config
from components.core.providers import BaseLLMProvider
from components.email.enums import EmailCategory
from components.email.schemas import ClassificationResultSchema
from components.third_party.anthropic.constants import _SYSTEM_PROMPT, _TOOL, ANTHROPIC_ERROR_CALL

cfg = get_config()


class AnthropicProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=cfg.ANTHROPIC_API_KEY)
        self._model = cfg.LLM_MODEL_NAME

    @classmethod
    def get(cls) -> "AnthropicProvider":
        return cls()

    async def classify(self, content: str) -> ClassificationResultSchema:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "classify_email"},
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "classify_email":
                data = block.input
                return ClassificationResultSchema(
                    category=EmailCategory(data["category"]),
                    confidence=float(data["confidence"]),
                    reasoning=data["reasoning"],
                    signals=data["signals"],
                )

        raise RuntimeError(ANTHROPIC_ERROR_CALL)
