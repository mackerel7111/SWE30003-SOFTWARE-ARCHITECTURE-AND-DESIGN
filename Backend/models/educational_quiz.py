from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType
from .quiz_feedback import QuizFeedback
from .quiz_question import QuizQuestion

class EducationalQuiz:
    """
    Represents a full educational quiz composed of ``QuizQuestion`` objects.

    Attributes
    ----------
    quizId : str
    title : str
    topic : str
    species : str
    difficultyLevel : str
        One of ``DIFFICULTY_*`` constants.
    questions : list[QuizQuestion]
    createdBy : str
        ``_id`` of the creating ``AssociationStaff``.
    """

    def __init__(
        self,
        title:           str,
        topic:           str,
        questions:       list[QuizQuestion],
        species:         str              = SPECIES_DOG,
        difficultyLevel: str              = DIFFICULTY_BEGINNER,
        createdBy:       str              = "",
        quizId:          str              = "",
        createdAt:       datetime | None  = None,
    ) -> None:
        """
        Initialise an ``EducationalQuiz``.

        Parameters
        ----------
        title : str
        topic : str
        questions : list[QuizQuestion]
            Must contain at least one question.
        difficultyLevel : str, optional
        createdBy : str, optional
        quizId : str, optional
        createdAt : datetime, optional
        """
        _requireNonEmpty(title, "title")
        _requireNonEmpty(topic, "topic")

        if not questions:
            raise ValueError("An educational quiz must have at least one question.")
        if species.lower() not in VALID_SPECIES:
            raise ValueError(f"Invalid species '{species}'. Must be one of {VALID_SPECIES}.")
        if difficultyLevel not in VALID_DIFFICULTIES:
            raise ValueError(
                f"Invalid difficultyLevel '{difficultyLevel}'. "
                f"Must be one of {VALID_DIFFICULTIES}."
            )

        self.quizId          = quizId
        self.title           = title.strip()
        self.topic           = topic.strip().lower()
        self.species         = species.strip().lower()
        self.questions       = questions
        self.difficultyLevel = difficultyLevel
        self.createdBy       = createdBy
        self.createdAt       = createdAt or datetime.now(timezone.utc)

    def calculateScore(self, submittedAnswers: dict[str, str]) -> int:
        score = 0

        for question in self.questions:
            selectedAnswer = submittedAnswers.get(question.questionId, "")
            if question.checkAnswer(selectedAnswer):
                score += 1

        return score
    
    @property
    def questionCount(self) -> int:
        """Return the number of questions in this quiz."""
        return len(self.questions)

    def getQuestions(self) -> list[QuizQuestion]:
        return self.questions

    def toDict(self) -> dict:
        """
        Serialise ``EducationalQuiz`` to a dict, including nested objects.

        Returns
        -------
        dict
        """
        return {
            "title":           self.title,
            "topic":           self.topic,
            "species":         self.species,
            "difficultyLevel": self.difficultyLevel,
            "questions":       [q.toDict() for q in self.questions],
            "createdBy":       self.createdBy,
            "createdAt":       self.createdAt,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "EducationalQuiz":
        """
        Construct an ``EducationalQuiz`` from a MongoDB document dict.

        Nested ``questions`` and ``feedbackList`` arrays are rehydrated
        into their respective domain objects.

        Parameters
        ----------
        data : dict

        Returns
        -------
        EducationalQuiz
        """
        questions    = [QuizQuestion.fromDict(q) for q in data.get("questions",    [])]
        return cls(
            title           = data.get("title",           ""),
            topic           = data.get("topic",           ""),
            species         = data.get("species",         SPECIES_DOG),
            questions       = questions if questions else [
                QuizQuestion(
                    "Q000",
                    "Placeholder",
                    ["A", "B"],
                    "A",
                    QuizFeedback("No feedback available."),
                )
            ],
            difficultyLevel = data.get("difficultyLevel", DIFFICULTY_BEGINNER),
            createdBy       = data.get("createdBy",       ""),
            quizId          = str(data.get("_id",         "")),
            createdAt       = data.get("createdAt"),
        )

    def __repr__(self) -> str:
        return (
            f"<EducationalQuiz title={self.title!r} "
            f"species={self.species!r} questions={self.questionCount} "
            f"difficulty={self.difficultyLevel!r}>"
        )
