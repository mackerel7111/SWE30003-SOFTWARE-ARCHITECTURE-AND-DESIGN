import logging
from datetime import datetime, timezone
from Backend.database import Database
from Backend.models import (
    PetOwner, AssociationStaff, VeterinaryPartner, PetProfile,
    FirstAidGuide, InstructionalVideo, VetDetails,
    RegionalAlert, ApprovalRequest, EducationalQuiz, QuizQuestion, QuizFeedback,
    ROLE_PET_OWNER, ROLE_ASSOCIATION_STAFF, ROLE_VET_PARTNER,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
)

logger = logging.getLogger(__name__)
from .content_repository import ContentRepository

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
