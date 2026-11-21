"""Build 10 sample .eml files (one or two per category) from the datasets in ./datasets.

Usage: python scripts/make_eml_samples.py [output_dir]   (default: datasets/eml)
"""

import csv
import random
import sys
from email.message import EmailMessage
from email.utils import format_datetime
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"
BASE_DATE = datetime(2026, 1, 15, 9, 30, tzinfo=timezone.utc)
rnd = random.Random(7)

csv.field_size_limit(10**9)


def read_csv(name: str) -> list[dict]:
    with open(DATASETS / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build(sender: str, to: str, subject: str, text: str, html: str | None = None, extra: dict | None = None) -> bytes:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, to, subject
    msg["Date"] = format_datetime(BASE_DATE + timedelta(hours=rnd.randint(0, 500)))
    msg["Message-ID"] = f"<{rnd.getrandbits(64):x}@example.com>"
    for k, v in (extra or {}).items():
        msg[k] = v
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    return bytes(msg)


def pick(rows: list[dict], label: str, n: int, max_len: int = 1200, keywords: tuple[str, ...] = ()) -> list[str]:
    pool = [
        r["text"] for r in rows
        if r["label"] == label and 80 < len(r["text"]) < max_len and (not keywords or any(k in r["text"].lower() for k in keywords))
    ]
    return rnd.sample(pool, n)


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DATASETS / "eml"
    out.mkdir(parents=True, exist_ok=True)

    emails = read_csv("phishing_emails_sample.csv")
    injections = [r for r in read_csv("prompt_injections.csv") if r["label"] == "1" and r["text"].isascii()
                  and any(k in r["text"].lower() for k in ("ignore", "forget all", "disregard"))]
    inj_texts = rnd.sample([r["text"] for r in injections if len(r["text"]) > 40], 2)

    files: dict[str, bytes] = {}

    # phishing (from dataset)
    for i, body in enumerate(pick(emails, "phishing", 2, keywords=("verify your", "password", "confirm your", "log in", "login")), 1):
        files[f"phishing_{i}.eml"] = build(
            "Account Security <security@acc0unt-verify.example>", "victim@example.com",
            "Urgent: verify your account", body,
        )

    # personal (legitimate emails from dataset)
    for i, body in enumerate(pick(emails, "legitimate", 2), 1):
        files[f"personal_{i}.eml"] = build("colleague@example.org", "me@example.com", "Re: follow-up", body)

    # prompt injection hidden inside an otherwise ordinary email
    for i, inj in enumerate(inj_texts, 1):
        files[f"prompt_injection_{i}.eml"] = build(
            "partner@example.net", "me@example.com", "Quick question about the invoice",
            f"Hi,\n\nCould you check the attached invoice when you have a minute?\n\n{inj}\n\nThanks,\nAlex",
        )

    # spam
    files["spam_1.eml"] = build(
        "deals@cheap-meds.example", "me@example.com", "!!! WIN a FREE iPhone - limited offer !!!",
        "CONGRATULATIONS! You have been selected to receive a FREE iPhone 17.\nBuy cheap meds online, "
        "100% guaranteed, no prescription. Click now: http://win-prize.example/claim\n\nUnsubscribe: reply STOP",
    )

    # newsletter
    files["newsletter_1.eml"] = build(
        "Weekly Digest <news@techweekly.example>", "me@example.com", "TechWeekly #212: this week in AI",
        "TechWeekly #212\n\n1. New open-source LLM released\n2. Python 3.14 highlights\n3. Cloud pricing changes\n\n"
        "You are receiving this because you subscribed. Unsubscribe: https://techweekly.example/unsub",
        html="<h1>TechWeekly #212</h1><ol><li>New open-source LLM</li><li>Python 3.14</li><li>Cloud pricing</li></ol>"
             "<p><a href='https://techweekly.example/unsub'>Unsubscribe</a></p>",
        extra={"List-Unsubscribe": "<https://techweekly.example/unsub>"},
    )

    # transactional
    files["transactional_1.eml"] = build(
        "Shop <orders@shop.example>", "me@example.com", "Your order #48213 has shipped",
        "Hello,\n\nYour order #48213 (1x Mechanical Keyboard, total $89.00) has shipped.\n"
        "Tracking number: 1Z999AA10123456784\nEstimated delivery: Jan 20.\n\nThank you for your purchase!",
    )

    # automated
    files["automated_1.eml"] = build(
        "CI Bot <noreply@ci.example>", "dev@example.com", "[CI] Build #1042 failed on main",
        "Pipeline #1042 for branch main failed.\nStage: test\nJob: pytest (exit code 1)\n"
        "See logs: https://ci.example/jobs/1042\n\nThis is an automated message, do not reply.",
        extra={"Auto-Submitted": "auto-generated"},
    )

    for name, data in files.items():
        (out / name).write_bytes(data)
    print(f"Wrote {len(files)} files to {out}")


if __name__ == "__main__":
    main()
