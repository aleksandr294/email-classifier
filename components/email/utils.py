import typing
import unicodedata

_KEEP_CONTROL = {"\n", "\t"}


def sanitize_text(text: str) -> str:
    """Normalize text before it reaches the LLM.

    - NFKC folds fullwidth / compatibility look-alikes ("ｉｇｎｏｒｅ" -> "ignore")
    - drops invisible and direction-control characters (zero-width, bidi overrides, tags, ...)
      that are used to hide or split instruction keywords
    """
    text = unicodedata.normalize("NFKC", text)
    return "".join(
        ch for ch in text if ch in _KEEP_CONTROL or unicodedata.category(ch) not in {"Cf", "Cc", "Co", "Cs", "Cn"}
    )


def sanitize_text_tree(value: typing.Any) -> typing.Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return {sanitize_text(str(k)): sanitize_text_tree(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_text_tree(v) for v in value]
    return value
