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
from .search_engine import SearchEngine

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
