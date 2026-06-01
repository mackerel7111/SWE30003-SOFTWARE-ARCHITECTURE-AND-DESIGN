from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType

class QuizFeedback:
    """
    Represents educational feedback shown after answering a quiz question.
    """

    def __init__(self, explanationText: str):
        _requireNonEmpty(explanationText, "explanationText")
        self.explanationText = explanationText.strip()

    def getExplanation(self) -> str:
        return self.explanationText

    def toDict(self) -> dict:
        return {
            "explanationText": self.explanationText,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "QuizFeedback":
        return cls(
            explanationText=data.get("explanationText", "")
        )

    def __repr__(self) -> str:
        return f"<QuizFeedback explanation={self.explanationText[:30]!r}>"
