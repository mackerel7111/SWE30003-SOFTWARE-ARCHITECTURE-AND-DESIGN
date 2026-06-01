"""
Domain / Entity Layer package.

Classes are split into individual files, while this package keeps the original
``from Backend.models import ...`` import style working for the rest of the app.
"""

from .common import (
    ROLE_PET_OWNER, ROLE_ASSOCIATION_STAFF, ROLE_VET_PARTNER, VALID_ROLES,
    SPECIES_DOG, SPECIES_CAT, SPECIES_RABBIT, SPECIES_HAMSTER,
    SPECIES_GUINEA_PIG, SPECIES_BIRD, SPECIES_TORTOISE, VALID_SPECIES,
    URGENCY_EMERGENCY, URGENCY_URGENT, URGENCY_NON_URGENT, VALID_URGENCY,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, VALID_STATUSES,
    DIFFICULTY_BEGINNER, DIFFICULTY_INTERMEDIATE, DIFFICULTY_ADVANCED,
    VALID_DIFFICULTIES, EMAIL_REGEX,
)
from .user import User
from .pet_owner import PetOwner
from .association_staff import AssociationStaff
from .veterinary_partner import VeterinaryPartner
from .pet_profile import PetProfile
from .symptom import Symptom
from .first_aid_guide import FirstAidGuide
from .instructional_video import InstructionalVideo
from .vet_details import VetDetails
from .regional_alert import RegionalAlert
from .approval_request import ApprovalRequest
from .quiz_feedback import QuizFeedback
from .quiz_question import QuizQuestion
from .educational_quiz import EducationalQuiz

__all__ = [
    "ROLE_PET_OWNER", "ROLE_ASSOCIATION_STAFF", "ROLE_VET_PARTNER", "VALID_ROLES",
    "SPECIES_DOG", "SPECIES_CAT", "SPECIES_RABBIT", "SPECIES_HAMSTER",
    "SPECIES_GUINEA_PIG", "SPECIES_BIRD", "SPECIES_TORTOISE", "VALID_SPECIES",
    "URGENCY_EMERGENCY", "URGENCY_URGENT", "URGENCY_NON_URGENT", "VALID_URGENCY",
    "STATUS_PENDING", "STATUS_APPROVED", "STATUS_REJECTED", "VALID_STATUSES",
    "DIFFICULTY_BEGINNER", "DIFFICULTY_INTERMEDIATE", "DIFFICULTY_ADVANCED",
    "VALID_DIFFICULTIES", "EMAIL_REGEX",
    "User", "PetOwner", "AssociationStaff", "VeterinaryPartner", "PetProfile",
    "Symptom", "FirstAidGuide", "InstructionalVideo", "VetDetails", "RegionalAlert",
    "ApprovalRequest", "QuizQuestion", "QuizFeedback", "EducationalQuiz",
]
