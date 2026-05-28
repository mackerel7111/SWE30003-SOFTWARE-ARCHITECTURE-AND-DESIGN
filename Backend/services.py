"""
services.py — Business Logic Layer
Pet First-Aid Web Application

This module coordinates application workflows by implementing the system's 
Control classes. It interfaces between the presentation/routing layer (app.py) 
and the domain entity/data layers (models.py, database.py).

Architecture tier : Business Logic Layer (Tier 3 of 5)
Conventions       : PascalCase classes · camelCase methods/attributes ·
                    UPPER_SNAKE_CASE constants · triple-quoted docstrings
"""

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


class AuthenticationManager:
    """
    Singleton Control class responsible for managing user sessions,
    authentication verification, and role-based access control (RBAC).
    """
    
    _instance = None

    def __new__(cls) -> "AuthenticationManager":
        """Enforce the Singleton pattern for the AuthenticationManager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db = Database()
        return cls._instance

    def authenticateUser(self, email: str, passwordPlain: str) -> dict | None:
        """
        Validate user credentials against stored records.
        
        Note: For this prototype implementation, a simplified plaintext check 
        is carried out. In a final production setup, this would use a secure 
        hashing library like bcrypt.

        Parameters
        ----------
        email : str
        passwordPlain : str

        Returns
        -------
        dict or None
            A session state dictionary containing basic user identity and role 
            if authentication is successful; None otherwise.
        """
        userDoc = self._db.findUserByEmail(email)
        if not userDoc or not userDoc.get("isActive"):
            return None

        # Prototype fallback password verification match
        if userDoc.get("passwordHash") == f"hashed_{passwordPlain}_placeholder" or userDoc.get("passwordHash") == passwordPlain:
            return {
                "userId": str(userDoc["_id"]),
                "email": userDoc["email"],
                "role": userDoc["role"],
                "fullName": userDoc["fullName"]
            }
        return None

    def verifyRole(self, sessionUser: dict | None, requiredRoles: list[str]) -> bool:
        """
        Enforce Role-Based Access Control (RBAC) constraints on a session user.

        Parameters
        ----------
        sessionUser : dict or None
            The current active session user details payload.
        requiredRoles : list[str]
            A collection of role identifiers authorized to perform an operation.

        Returns
        -------
        bool
            True if the user session is active and possesses a required role; 
            False otherwise.
        """
        if not sessionUser:
            return False
        return sessionUser.get("role") in requiredRoles

class TriageEngine:
    """
    Control class designed to evaluate reported symptoms against animal species parameters 
    and establish the baseline urgency rating.
    """
    def __init__(self):
        self.searchEngine = SearchEngine()

    def evaluateSymptoms(self, species: str, symptomNames: list[str]) -> dict:
        if not symptomNames:
            return {
                "urgencyLevel": "NON_URGENT",
                "triageNotes": "No visible symptoms reported. Continue monitoring your pet's routine behaviors closely."
            }

        matchedUrgencyLevels = []
        normalizedSpecies = species.lower().strip()

        for symptomName in symptomNames:
            guides = self.searchEngine.queryFirstAidGuides(
                normalizedSpecies,
                symptomName
            )

            for guide in guides:
                matchedUrgencyLevels.append(guide.urgencyLevel)

        if "EMERGENCY" in matchedUrgencyLevels:
            return {
                "urgencyLevel": "EMERGENCY",
                "triageNotes": "CRITICAL SITUATION DETECTED. Please immediately check the relevant emergency first-aid guides and transport your pet safely to an open emergency care clinic."
            }

        elif "URGENT" in matchedUrgencyLevels:
            return {
                "urgencyLevel": "URGENT",
                "triageNotes": "Potentially hazardous condition. Apply preliminary stabilised care steps and secure a veterinary consultation within the day."
            }

        return {
            "urgencyLevel": "NON_URGENT",
            "triageNotes": "Symptoms appear to indicate mild complications. Administer standard comfort care routines, but consult a professional vet if conditions worsen."
        }


class SearchEngine:
    """
    Control class for matching user input text expressions with available
    veterinary services and published documentation assets.
    """

    def __init__(self):
        self.contentRepository = ContentRepository()

    def searchVetsByRegion(self, region: str) -> list[VetDetails]:
        """
        Find authorised veterinary clinics located in a target region.
        """
        return self.contentRepository.getVetDetailsByRegion(region)

    def queryFirstAidGuides(self, species: str, userQueryText: str) -> list[FirstAidGuide]:
        """
        Execute keyword search against published first-aid guides.
        """
        tokens = self._tokenizeSearchText(userQueryText)
        return self.contentRepository.getFirstAidGuides(species, tokens)

    def _tokenizeSearchText(self, userQueryText: str) -> list[str]:
        """
        Convert a raw user search string into searchable keyword tokens.
        """
        tokens = [
            token.lower().strip()
            for token in userQueryText.split()
            if len(token) > 2
        ]

        if not tokens:
            tokens = [userQueryText.lower().strip()]

        return tokens


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


class ContentModerator:
    """
    Control class managing workflows for content verification, vetting loops, 
    and approval queues for material submitted by verified vets.
    """

    def initiateSubmission(self, vetUserId: str, contentType: str, contentDataPayload: dict) -> str:
        """
        Log content submissions into review queues, waiting for internal audits.

        Parameters
        ----------
        vetUserId : str
        contentType : str
        contentDataPayload : dict

        Returns
        -------
        str
            The tracking key identifier string for the generated proposal.
        """
        requestObj = ApprovalRequest(
            submittedBy=vetUserId,
            contentType=contentType,
            contentData=contentDataPayload
        )
        db = Database()
        return db.insertApprovalRequest(requestObj.toDict())

    def getPendingQueue(self) -> list[ApprovalRequest]:
        """
        Fetch all incoming content changes still requiring confirmation.

        Returns
        -------
        list[ApprovalRequest]
        """
        db = Database()
        rawRequests = db.findApprovalRequestsByStatus(STATUS_PENDING)
        return [ApprovalRequest.fromDict(req) for req in rawRequests]

    def processReviewDecision(self, requestId: str, staffUserId: str, finalStatus: str, notes: str = "") -> bool:
        """
        Apply an atomic lifecycle status update to a submission request. If approved, 
        the data is compiled and written out to active content collections.

        Parameters
        ----------
        requestId : str
        staffUserId : str
        finalStatus : str
            Must be either STATUS_APPROVED or STATUS_REJECTED.
        notes : str, optional

        Returns
        -------
        bool
            True if status changes were applied safely; False otherwise.
        """
        if finalStatus not in (STATUS_APPROVED, STATUS_REJECTED):
            raise ValueError(f"Invalid outcome option assignment: {finalStatus}")

        db = Database()
        updatedDoc = db.updateApprovalStatus(requestId, finalStatus, staffUserId, notes)
        if not updatedDoc:
            return False

        # If the content is approved, deploy it to active production tables
        if finalStatus == STATUS_APPROVED:
            contentType = updatedDoc.get("contentType")
            contentData = updatedDoc.get("contentData", {})

            if contentType == "first_aid_guide":
                contentData["isApproved"] = True
                contentData["approvedBy"] = staffUserId
                db.insertFirstAidGuide(contentData)
            elif contentType == "instructional_video":
                contentData["isApproved"] = True
                contentData["viewCount"] = 0
                db.insertVideo(contentData)
                
        return True


class AlertBroadcaster:
    """
    Control class for creating regional alert records and retrieving active alerts
    by region for database-backed in-app display.
    """

    def distributeNewAlert(self, staffUserId: str, title: str, description: str, region: str, severity: str) -> str:
        """
        Create a regional alert record and persist it for later retrieval by users
        in the affected region.

        Parameters
        ----------
        staffUserId : str
        title : str
        description : str
        region : str
        severity : str

        Returns
        -------
        str
            The identifier key of the broadcast document record.
        """
        alertObj = RegionalAlert(
            title=title,
            description=description,
            region=region,
            severity=severity,
            isActive=True,
            createdBy=staffUserId
        )
        db = Database()
        return db.insertAlert(alertObj.toDict())

    def fetchLocalAlerts(self, region: str) -> list[RegionalAlert]:
        """
        Collect active hazard indicators impacting a particular region.

        Parameters
        ----------
        region : str

        Returns
        -------
        list[RegionalAlert]
        """
        db = Database()
        rawAlerts = db.findActiveAlertsByRegion(region)
        return [RegionalAlert.fromDict(alert) for alert in rawAlerts]
