from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType
from .quiz_feedback import QuizFeedback

class QuizQuestion:
    """
    Represents a single multiple-choice question within an ``EducationalQuiz``.

    Attributes
    ----------
    questionId : str
    questionText : str
    options : list[str]
        Answer options, typically prefixed ``"A."`` through ``"D."``.
    correctAnswer : str
        The key of the correct option (e.g. ``"A"``).
    explanation : str
        Shown to the user after they answer.
    """

    def __init__(
        self,
        questionId:    str,
        questionText:  str,
        options:       list[str],
        correctAnswer: str,
        feedback:QuizFeedback,
    ) -> None:
        """
        Initialise a ``QuizQuestion``.

        Parameters
        ----------
        questionId : str
        questionText : str
        options : list[str]
            Must contain at least two options.
        correctAnswer : str
        explanation : str, optional
        """
        _requireNonEmpty(questionId,   "questionId")
        _requireNonEmpty(questionText, "questionText")
        _requireNonEmpty(correctAnswer,"correctAnswer")

        if not options or len(options) < 2:
            raise ValueError("A quiz question must have at least two answer options.")

        self.questionId    = questionId
        self.questionText  = questionText.strip()
        self.options       = options
        self.correctAnswer = correctAnswer.strip().upper()
        self.feedback   = feedback
        
    def checkAnswer(self, selectedAnswer: str) -> bool:
        return selectedAnswer.strip().upper() == self.correctAnswer
    
    def getFeedback(self) -> str:
        return self.feedback.getExplanation()

    def toDict(self) -> dict:
        """
        Serialise ``QuizQuestion`` to a dict.

        Returns
        -------
        dict
        """
        return {
            "questionId":    self.questionId,
            "questionText":  self.questionText,
            "options":       self.options,
            "correctAnswer": self.correctAnswer,
            "feedback":      self.feedback.toDict(),
        }

    @classmethod
    def fromDict(cls, data: dict) -> "QuizQuestion":
        """
        Construct a ``QuizQuestion`` from a dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        QuizQuestion
        """
        feedbackData = data.get("feedback", {"explanationText": data.get("explanation", "")})
        if isinstance(feedbackData, str):
            feedbackData = {"explanationText": feedbackData}

        return cls(
            questionId    = data.get("questionId",    ""),
            questionText  = data.get("questionText",  ""),
            options       = data.get("options",       ["", ""]),
            correctAnswer = data.get("correctAnswer", ""),
            feedback      = QuizFeedback.fromDict(feedbackData),
        )

    def __repr__(self) -> str:
        return f"<QuizQuestion id={self.questionId!r}>"
