import factory.fuzzy
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

from components.email.enums import EmailCategory, EmailStatus
from components.email.models import Email

fake = Faker()


class EmailFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Email

    content_hash = factory.Faker("sha256")
    file_path = factory.LazyAttribute(lambda obj: f"/tmp/emails/{obj.content_hash}.eml")
    status = EmailStatus.PENDING
    category = None
    confidence = None
    reasoning = None
    signals = None
    reviewed = False
    injection_detected = False

    class Params:
        classified = factory.Trait(
            status=EmailStatus.CLASSIFIED,
            category=factory.fuzzy.FuzzyChoice(list(EmailCategory)),
            confidence=factory.fuzzy.FuzzyFloat(0.6, 1.0),
            reasoning=factory.Faker("sentence"),
            signals=factory.LazyFunction(lambda: [fake.word() for _ in range(3)]),
        )

        failed = factory.Trait(
            status=EmailStatus.FAILED,
        )

        classified_spam = factory.Trait(
            status=EmailStatus.CLASSIFIED,
            category=EmailCategory.SPAM,
            confidence=factory.fuzzy.FuzzyFloat(0.6, 1.0),
            reasoning=factory.Faker("sentence"),
            signals=factory.LazyFunction(lambda: [fake.word() for _ in range(2)]),
        )

        low_confidence = factory.Trait(
            status=EmailStatus.CLASSIFIED,
            category=factory.fuzzy.FuzzyChoice(list(EmailCategory)),
            confidence=factory.fuzzy.FuzzyFloat(0.0, 0.59),
            reasoning=factory.Faker("sentence"),
            signals=factory.LazyFunction(lambda: [fake.word() for _ in range(2)]),
            reviewed=True,
        )
