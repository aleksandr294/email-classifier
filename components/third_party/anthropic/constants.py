from components.email.enums import EmailCategory

_TOOL = {
    "name": "classify_email",
    "description": "Classify the email into a category with confidence score and reasoning.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": [category.value for category in EmailCategory],
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score between 0.0 and 1.0",
            },
            "reasoning": {
                "type": "string",
                "description": "Explanation of why this category was chosen",
            },
            "signals": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key signals that led to this classification",
            },
        },
        "required": ["category", "confidence", "reasoning", "signals"],
    },
}


_SYSTEM_PROMPT = """You are an email classification expert. Analyze the provided email and classify it into exactly one category:

- spam: Unwanted bulk email, advertisements, or unsolicited promotions
- phishing: Fraudulent emails attempting to steal credentials or personal information
- newsletter: Subscription-based informational or marketing emails with unsubscribe option
- transactional: Automated emails triggered by user actions (receipts, confirmations, shipping)
- personal: Direct person-to-person communication
- automated: System-generated emails (alerts, reports, digests) not covered by other categories

Base your classification on the email headers, subject, sender, and body content."""


ANTHROPIC_ERROR_CALL = "Anthropic did not return a classification tool call"
