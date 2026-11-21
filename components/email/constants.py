MIN_CONFIDENCE_VALUE = 0.6
MAX_EMAIL_BODY_CHARS = 20_000
PROMPT_HEADERS = (
    "Reply-To",
    "Return-Path",
    "Sender",
    "List-Unsubscribe",
    "Auto-Submitted",
    "Precedence",
    "X-Mailer",
)

SPAM_EML = (
    b"From: spammer@cheap-deals.xyz\r\n"
    b"To: victim@example.com\r\n"
    b"Subject: YOU WON $1,000,000!!!\r\n"
    b"Date: Mon, 19 May 2026 08:00:00 +0000\r\n"
    b"MIME-Version: 1.0\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n"
    b"\r\n"
    b"Congratulations! Click here to claim your prize: http://totally-not-scam.xyz\r\n"
)
