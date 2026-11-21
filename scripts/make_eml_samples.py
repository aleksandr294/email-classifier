"""Build 35 sample .eml files (5 per category, 7 categories) from the datasets in ./datasets.

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
        if "trump" not in r["text"].lower() and r["label"] == label and 80 < len(r["text"]) < max_len and (not keywords or any(k in r["text"].lower() for k in keywords))
    ]
    return rnd.sample(pool, n)


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DATASETS / "eml"
    out.mkdir(parents=True, exist_ok=True)

    emails = read_csv("phishing_emails_sample.csv")
    injections = [
        r for r in read_csv("prompt_injections.csv")
        if r["label"] == "1" and r["text"].isascii() and len(r["text"]) > 40
        and any(k in r["text"].lower() for k in ("ignore", "forget all", "disregard"))
    ]
    inj_texts = rnd.sample([r["text"] for r in injections], 5)

    files: dict[str, bytes] = {}

    # phishing
    phishing = [
        ("Account Security <security@acc0unt-verify.example>", "Urgent: verify your account",
         "Dear customer,\n\nWe detected unusual activity on your account. Your account will be suspended in 24 hours "
         "unless you verify your identity.\n\nVerify now: http://acc0unt-verify.example/login?id=88213\n\nSecurity Team"),
        ("PayPaI Support <help@paypa1-secure.example>", "Your payment was declined - action required",
         "Your recent payment of $349.99 was declined. Update your billing information and confirm your card "
         "number and CVV to avoid account limitation: http://paypa1-secure.example/update"),
        ("IT Helpdesk <it-support@corp-mail-reset.example>", "Password expires today",
         "Your corporate email password expires today. Log in to keep your current password: "
         "http://corp-mail-reset.example/owa\nFailure to do so will result in loss of mailbox access."),
        ("Bank Alert <alert@secure-bank-login.example>", "Suspicious sign-in detected",
         "We blocked a sign-in to your online banking from an unknown device (Lagos, NG). If this was not you, "
         "confirm your username, password and one-time code here: http://secure-bank-login.example/verify"),
        ("Apple ID <noreply@appleid-confirm.example>", "Confirm your Apple ID",
         "Your Apple ID has been locked for security reasons. Click the link below and enter your Apple ID, "
         "password and credit card details to unlock it: http://appleid-confirm.example/unlock"),
    ]
    for i, (sender, subj, text) in enumerate(phishing, 1):
        files[f"phishing_{i}.eml"] = build(sender, "victim@example.com", subj, text)

    # personal (legitimate human-written emails from dataset)
    personal_bodies = pick(emails, "legitimate", 5, keywords=("thanks", "please", "meeting", "call", "let me know"), max_len=2500)
    for i, body in enumerate(personal_bodies, 1):
        files[f"personal_{i}.eml"] = build("colleague@example.org", "me@example.com", "Re: follow-up", body)

    # prompt injection hidden inside an otherwise ordinary email
    inj_subjects = ["Quick question about the invoice", "Meeting notes", "Re: project status", "Contract draft", "Lunch?"]
    for i, (inj, subj) in enumerate(zip(inj_texts, inj_subjects), 1):
        files[f"prompt_injection_{i}.eml"] = build(
            "partner@example.net", "me@example.com", subj,
            f"Hi,\n\nCould you take a look when you have a minute?\n\n{inj}\n\nThanks,\nAlex",
        )

    # spam
    spam = [
        ("deals@cheap-meds.example", "!!! WIN a FREE iPhone - limited offer !!!",
         "CONGRATULATIONS! You have been selected to receive a FREE iPhone 17.\nBuy cheap meds online, "
         "100% guaranteed, no prescription. Click now: http://win-prize.example/claim\n\nUnsubscribe: reply STOP"),
        ("promo@casino-royal.example", "You won $1,000,000!!!", "Claim your casino bonus NOW! 500 free spins, no deposit. http://spin.example/win"),
        ("boss@work-from-home.example", "Earn $5000/week from home", "Make money fast! No experience needed. Join 10,000 happy members today: http://rich.example"),
        ("pharma@rx-discount.example", "Viagra 90% OFF", "Cheap generic pills, discreet shipping, no prescription needed. Order now http://pills.example"),
        ("seo@rank-booster.example", "Get 100k visitors to your website", "We guarantee #1 Google rank in 7 days! Buy 1M backlinks for only $9. Reply for a special price."),
    ]
    for i, (sender, subj, text) in enumerate(spam, 1):
        files[f"spam_{i}.eml"] = build(sender, "me@example.com", subj, text)

    # newsletter
    newsletters = [
        ("TechWeekly #212: this week in AI", "TechWeekly", "news@techweekly.example",
         ["New open-source LLM released", "Python 3.14 highlights", "Cloud pricing changes"]),
        ("The Morning Brief - Nov 21", "Morning Brief", "brief@morningbrief.example",
         ["Markets open higher", "Climate summit update", "Five stories you missed"]),
        ("DevDigest: 10 tips for faster builds", "DevDigest", "hello@devdigest.example",
         ["Caching dependencies", "Parallel test runs", "Slimmer Docker images"]),
        ("Cooking Club: autumn recipes", "Cooking Club", "club@cookingclub.example",
         ["Pumpkin soup", "Apple crumble", "One-pan chicken"]),
        ("Design Notes Monthly", "Design Notes", "editor@designnotes.example",
         ["Typography trends", "Dark mode done right", "Interview: a product designer"]),
    ]
    for i, (subj, name, addr, items) in enumerate(newsletters, 1):
        domain = addr.split("@")[1]
        lines = "\n".join(f"{n}. {t}" for n, t in enumerate(items, 1))
        li = "".join(f"<li>{t}</li>" for t in items)
        files[f"newsletter_{i}.eml"] = build(
            f"{name} <{addr}>", "me@example.com", subj,
            f"{subj}\n\n{lines}\n\nYou are receiving this because you subscribed. Unsubscribe: https://{domain}/unsub",
            html=f"<h1>{subj}</h1><ol>{li}</ol><p><a href='https://{domain}/unsub'>Unsubscribe</a></p>",
            extra={"List-Unsubscribe": f"<https://{domain}/unsub>"},
        )

    # transactional
    transactional = [
        ("Shop <orders@shop.example>", "Your order #48213 has shipped",
         "Hello,\n\nYour order #48213 (1x Mechanical Keyboard, total $89.00) has shipped.\n"
         "Tracking number: 1Z999AA10123456784\nEstimated delivery: Jan 20.\n\nThank you for your purchase!"),
        ("Billing <billing@saas.example>", "Receipt for your payment", "Thanks for your payment of $29.00 for the Pro plan (Jan 2026).\nInvoice #INV-20931 is attached to your account."),
        ("Airline <booking@flyair.example>", "Booking confirmation XK7L2P", "Your flight KBP -> WAW on Feb 3, 07:45 is confirmed.\nBooking reference: XK7L2P. Check-in opens 24h before departure."),
        ("Accounts <no-reply@service.example>", "Password reset requested", "We received a request to reset your password. Use this code: 482913. It expires in 15 minutes. If this wasn't you, ignore this email."),
        ("Hotel <reservations@stay.example>", "Reservation confirmed", "Your reservation at Stay Inn (Mar 5-8, 2 guests) is confirmed. Confirmation number: 77412."),
    ]
    for i, (sender, subj, text) in enumerate(transactional, 1):
        files[f"transactional_{i}.eml"] = build(sender, "me@example.com", subj, text)

    # automated
    automated = [
        ("CI Bot <noreply@ci.example>", "[CI] Build #1042 failed on main",
         "Pipeline #1042 for branch main failed.\nStage: test\nJob: pytest (exit code 1)\nSee logs: https://ci.example/jobs/1042\n\nThis is an automated message, do not reply."),
        ("Monitoring <alerts@monitor.example>", "[ALERT] CPU > 90% on web-03", "Host web-03 CPU usage 94% for 10 minutes.\nThreshold: 90%. Dashboard: https://monitor.example/h/web-03"),
        ("Cron <root@server.example>", "Cron <root@srv1> /usr/local/bin/backup.sh", "Backup completed: 12.4 GB, duration 00:14:32, status OK."),
        ("GitHub <notifications@github.example>", "[repo] Dependabot: bump requests from 2.31 to 2.32", "Dependabot opened pull request #88. Bumps requests from 2.31.0 to 2.32.0. This is an automated notification."),
        ("Calendar <calendar-noreply@cal.example>", "Reminder: Standup at 10:00", "Event: Daily standup. Time: 10:00-10:15 UTC. Join: https://meet.example/standup. Automatically generated reminder."),
    ]
    for i, (sender, subj, text) in enumerate(automated, 1):
        files[f"automated_{i}.eml"] = build(sender, "dev@example.com", subj, text, extra={"Auto-Submitted": "auto-generated"})

    for old in out.glob("*.eml"):
        old.unlink()
    for name, data in files.items():
        (out / name).write_bytes(data)
    print(f"Wrote {len(files)} files to {out}")


if __name__ == "__main__":
    main()
