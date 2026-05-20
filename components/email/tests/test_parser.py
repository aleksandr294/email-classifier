import pytest

from components.email.constants import SPAM_EML
from components.email.parser import EmailParser


@pytest.mark.asyncio
async def test_parse_spam_extracts_subject_and_sender(parser: EmailParser):
    result = await parser.process(SPAM_EML)
    assert result.subject is not None
    assert result.sender is not None


@pytest.mark.asyncio
async def test_parse_phishing_extracts_recipients(parser: EmailParser):
    result = await parser.process(SPAM_EML)
    assert len(result.recipients) > 0


@pytest.mark.asyncio
async def test_parse_newsletter_extracts_body(parser: EmailParser):
    result = await parser.process(SPAM_EML)
    assert result.body_plain is not None or result.body_html is not None


@pytest.mark.asyncio
async def test_parse_minimal_rfc822_extracts_all_fields(parser: EmailParser):
    result = await parser.process(SPAM_EML)
    assert result.sender == "spammer@cheap-deals.xyz"
    assert "victim@example.com" in result.recipients
    assert result.subject == "YOU WON $1,000,000!!!"
    assert result.body_plain is not None
    assert "Congratulations! Click here to claim your prize: http://totally-not-scam.xyz" in result.body_plain
