import enum


class EmailStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    CLASSIFIED = "classified"
    FAILED = "failed"


class EmailCategory(enum.StrEnum):
    SPAM = "spam"
    PHISHING = "phishing"
    NEWSLETTER = "newsletter"
    TRANSACTIONAL = "transactional"
    PERSONAL = "personal"
    AUTOMATED = "automated"
