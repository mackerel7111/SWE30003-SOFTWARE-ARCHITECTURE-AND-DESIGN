from flask import Flask

from Backend.database import Database
from Backend.models import (
    PetOwner,
    PetProfile,
    ROLE_ASSOCIATION_STAFF,
    ROLE_PET_OWNER,
    ROLE_VET_PARTNER,
    STATUS_APPROVED,
    STATUS_REJECTED,
    URGENCY_EMERGENCY,
    URGENCY_NON_URGENT,
    URGENCY_URGENT,
    VeterinaryPartner,
)
from Backend.services import (
    AlertBroadcaster,
    AuthenticationManager,
    ContentRepository,
    ContentModerator,
    SearchEngine,
    TriageEngine,
)


app = Flask(__name__)
app.secret_key = "pet-first-aid-dev-key"

database = Database()

authentication_manager = AuthenticationManager()
search_engine = SearchEngine()
triage_engine = TriageEngine()
alert_broadcaster = AlertBroadcaster()
content_moderator = ContentModerator()
content_repository = ContentRepository()

ROLE_LABELS = {
    ROLE_PET_OWNER: "PetOwner",
    ROLE_ASSOCIATION_STAFF: "AssociationStaff",
    ROLE_VET_PARTNER: "VeterinaryPartner",
}

URGENCY_FROM_FORM = {
    "Low": URGENCY_NON_URGENT,
    "Medium": URGENCY_URGENT,
    "High": URGENCY_EMERGENCY,
}

URGENCY_TO_TEMPLATE = {
    URGENCY_NON_URGENT: "Low",
    URGENCY_URGENT: "Medium",
    URGENCY_EMERGENCY: "High",
}

DEMO_LOGIN_ALIASES = {
    ("owner@example.com", "ownerpass"): ("owner@example.com", "owner_password"),
    ("staff@example.com", "staffpass"): ("admin@petfirstaid.org", "admin_password"),
    ("vet@example.com", "vetpass"): ("dr.tan@vetclinic.com", "vet1_password"),
}

SUPPORTED_SPECIES = ["dog", "cat", "rabbit", "hamster", "guinea pig", "bird", "tortoise"]
QUIZ_TOPICS = [
    ("breathing", "Breathing Difficulty"),
    ("bleeding", "Bleeding / Wound Care"),
    ("digestive", "Vomiting / Digestive Issues"),
    ("injury", "Limping / Injury"),
    ("skin", "Skin Irritation"),
]
