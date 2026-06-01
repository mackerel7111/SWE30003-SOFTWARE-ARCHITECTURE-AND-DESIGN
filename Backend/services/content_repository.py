import logging
from datetime import datetime, timezone
from Backend.database import Database
from Backend.models import (
    PetOwner, AssociationStaff, VeterinaryPartner, PetProfile,
    Symptom, FirstAidGuide, InstructionalVideo, VetDetails,
    RegionalAlert, ApprovalRequest, EducationalQuiz, QuizQuestion, QuizFeedback,
    ROLE_PET_OWNER, ROLE_ASSOCIATION_STAFF, ROLE_VET_PARTNER,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
)

logger = logging.getLogger(__name__)


class ContentRepository:
    """
    Control layer manager handling retrieval workflows for educational courses,
    media components, and public diagnostic tool metrics.

    This class also acts as a Factory for creating content entity objects from
    database records.
    """

    CONTENT_FIRST_AID_GUIDE = "first_aid_guide"
    CONTENT_INSTRUCTIONAL_VIDEO = "instructional_video"
    CONTENT_VET_DETAILS = "vet_details"
    CONTENT_EDUCATIONAL_QUIZ = "educational_quiz"

    def createContentObject(self, contentType: str, data: dict):
        """
        Factory Method for creating content entity objects from raw database data.
        """
        if contentType == self.CONTENT_FIRST_AID_GUIDE:
            return FirstAidGuide.fromDict(data)

        if contentType == self.CONTENT_INSTRUCTIONAL_VIDEO:
            return InstructionalVideo.fromDict(data)

        if contentType == self.CONTENT_VET_DETAILS:
            return VetDetails.fromDict(data)

        if contentType == self.CONTENT_EDUCATIONAL_QUIZ:
            return EducationalQuiz.fromDict(data)

        raise ValueError(f"Unknown content type: {contentType}")

    def getFirstAidGuides(self, species: str, keywords: list[str]) -> list[FirstAidGuide]:
        """
        Retrieve approved first-aid guides matching species and keywords.
        """
        db = Database()
        rawGuides = db.searchFirstAidGuides(species, keywords)

        return [
            self.createContentObject(self.CONTENT_FIRST_AID_GUIDE, guide)
            for guide in rawGuides
            if guide.get("isApproved")
        ]

    def getVetDetailsByRegion(self, region: str) -> list[VetDetails]:
        """
        Retrieve active veterinary clinic details for a region.
        """
        db = Database()
        rawVets = db.findVetsByRegion(region)

        return [
            self.createContentObject(self.CONTENT_VET_DETAILS, vet)
            for vet in rawVets
        ]

    def addVetDetails(self, clinicData: dict, staffUserId: str) -> str:
        """
        Create and persist a staff-maintained veterinary clinic directory record.
        """
        clinicData["createdByStaffId"] = staffUserId

        vetDetails = self.createContentObject(
            self.CONTENT_VET_DETAILS,
            clinicData
        )

        db = Database()
        return db.insertVetDetails(vetDetails.toDict())

    def getApprovedVideos(self, species: str) -> list[InstructionalVideo]:
        """
        Fetch educational videos cleared by staff for explicit animal categories.
        """
        db = Database()
        rawVideos = db.findVideosBySpecies(species)

        return [
            self.createContentObject(self.CONTENT_INSTRUCTIONAL_VIDEO, video)
            for video in rawVideos
        ]

    def getQuizDetails(self, quizId: str) -> EducationalQuiz | None:
        """
        Retrieve structured data layouts and questions associated with a quiz.
        """
        db = Database()
        rawQuiz = db.findQuizById(quizId)

        if rawQuiz:
            return self.createContentObject(
                self.CONTENT_EDUCATIONAL_QUIZ,
                rawQuiz
            )

        return None

    def getAllQuizzes(self) -> list[EducationalQuiz]:
        """
        Retrieve all available educational quizzes.
        """
        db = Database()

        return [
            self.createContentObject(self.CONTENT_EDUCATIONAL_QUIZ, quiz)
            for quiz in db.findAllQuizzes()
        ]

    def submitQuizResults(self, quizId: str, submittedAnswers: dict[str, str]) -> dict:
        quiz = self.getQuizDetails(quizId)

        if quiz is None:
            raise ValueError("Quiz not found.")

        score = quiz.calculateScore(submittedAnswers)

        questionResults = []
        for question in quiz.getQuestions():
            selectedAnswer = submittedAnswers.get(question.questionId, "")
            questionResults.append({
                "questionId": question.questionId,
                "selectedAnswer": selectedAnswer,
                "correctAnswer": question.correctAnswer,
                "isCorrect": question.checkAnswer(selectedAnswer),
                "feedback": question.getFeedback(),
            })

        return {
            "quizId": quiz.quizId,
            "score": score,
            "totalQuestions": quiz.questionCount,
            "questionResults": questionResults,
        }
