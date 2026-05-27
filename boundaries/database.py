"""
database.py — Data Access Layer
Pet First-Aid Web Application

Singleton Database class that acts as the exclusive gateway to the MongoDB
instance. All collection access, query execution, and write operations are
centralised here to enforce a single connection pool.
"""

import logging
from datetime import datetime, timezone

import pymongo
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MONGO_URI      = "mongodb://localhost:27017/"
DATABASE_NAME  = "pet_first_aid_db"

COLLECTION_USERS    = "Users"
COLLECTION_FIRST_AID = "FirstAidGuides"
COLLECTION_VIDEOS   = "InstructionalVideos"
COLLECTION_CLINICS  = "VetDetails"
COLLECTION_ALERTS   = "RegionalAlerts"
COLLECTION_APPROVALS = "ApprovalRequests"

logger = logging.getLogger(__name__)


class Database:
    """
    Singleton Data Access Layer wrapping a single pymongo MongoClient.
    Only one instance is ever created per interpreter session.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialise()
        return cls._instance

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _initialise(self):
        self._client = MongoClient(MONGO_URI)
        self._db     = self._client[DATABASE_NAME]

        self._users     = self._db[COLLECTION_USERS]
        self._firstAid  = self._db[COLLECTION_FIRST_AID]
        self._videos    = self._db[COLLECTION_VIDEOS]
        self._clinics   = self._db[COLLECTION_CLINICS]
        self._alerts    = self._db[COLLECTION_ALERTS]
        self._approvals = self._db[COLLECTION_APPROVALS]

        self._create_indexes()
        logger.info("Database Singleton initialised.")

    def _create_indexes(self):
        self._users.create_index([("email_address", ASCENDING)], unique=True, name="idx_users_email")
        self._alerts.create_index([("target_region", ASCENDING)], name="idx_alerts_region")
        self._approvals.create_index([("status", ASCENDING)], name="idx_approvals_status")
        self._firstAid.create_index([("emergency_category", ASCENDING)], name="idx_guides_category")
        self._clinics.create_index([("region", ASCENDING)], name="idx_clinics_region")

    # ------------------------------------------------------------------
    # Legacy connect/disconnect (kept for compatibility with main.py)
    # ------------------------------------------------------------------

    def connect(self):
        self.connection_status = True
        return True

    def disconnect(self):
        self.connection_status = False
        return False

    # ------------------------------------------------------------------
    # USER METHODS
    # ------------------------------------------------------------------

    def execute_query(self, query_type, criteria=None):
        if query_type == "find_user_by_email":
            return self.find_user_by_email(criteria)
        if query_type == "get_all_users":
            return list(self._users.find({}))
        return None

    def execute_update(self, update_type, data=None):
        if update_type == "add_user":
            return self._insert_user_object(data)
        return False

    def _insert_user_object(self, user_obj):
        """Insert a user entity object into MongoDB."""
        doc = {
            "user_id":       user_obj.user_id,
            "email_address": user_obj.email_address,
            "_password":     user_obj._password,
            "role":          user_obj.__class__.__name__,
        }

        # Role-specific fields
        if hasattr(user_obj, "home_location"):
            doc["home_location"] = user_obj.home_location
            doc["phone_number"]  = user_obj.phone_number

        if hasattr(user_obj, "employee_id"):
            doc["employee_id"]    = user_obj.employee_id
            doc["clearance_level"] = user_obj.clearance_level

        if hasattr(user_obj, "vet_id"):
            doc["vet_id"]         = user_obj.vet_id
            doc["license_number"] = user_obj.license_number

        try:
            self._users.update_one(
                {"email_address": user_obj.email_address},
                {"$setOnInsert": doc},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error("Failed to insert user: %s", e)
            return False

    def find_user_by_email(self, email_address):
        """Return a user entity object reconstructed from MongoDB."""
        doc = self._users.find_one({"email_address": email_address})
        if doc is None:
            return None
        return self._doc_to_user(doc)

    def _doc_to_user(self, doc):
        """Reconstruct the correct entity class from a MongoDB document."""
        from entities.pet_owner import PetOwner
        from entities.association_staff import AssociationStaff
        from entities.veterinary_partner import VeterinaryPartner

        role = doc.get("role")

        if role == "PetOwner":
            user = PetOwner(
                user_id=doc["user_id"],
                email_address=doc["email_address"],
                password=doc["_password"],
                home_location=doc.get("home_location", ""),
                phone_number=doc.get("phone_number", ""),
            )
        elif role == "AssociationStaff":
            user = AssociationStaff(
                user_id=doc["user_id"],
                email_address=doc["email_address"],
                password=doc["_password"],
                employee_id=doc.get("employee_id", ""),
                clearance_level=doc.get("clearance_level", 1),
            )
        elif role == "VeterinaryPartner":
            user = VeterinaryPartner(
                user_id=doc["user_id"],
                email_address=doc["email_address"],
                password=doc["_password"],
                vet_id=doc.get("vet_id", ""),
                license_number=doc.get("license_number", ""),
            )
        else:
            return None

        return user

    # ------------------------------------------------------------------
    # FIRST AID GUIDE METHODS
    # ------------------------------------------------------------------

    def get_all_guides(self):
        return list(self._firstAid.find({}))

    def get_guides_by_category(self, category):
        return list(self._firstAid.find({"emergency_category": category.lower()}))

    def insert_guide(self, guide_doc):
        try:
            self._firstAid.update_one(
                {"guide_id": guide_doc["guide_id"]},
                {"$setOnInsert": guide_doc},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error("Failed to insert guide: %s", e)
            return False

    # ------------------------------------------------------------------
    # INSTRUCTIONAL VIDEO METHODS
    # ------------------------------------------------------------------

    def get_all_videos(self):
        return list(self._videos.find({}))

    def insert_video(self, video_doc):
        try:
            self._videos.update_one(
                {"video_id": video_doc["video_id"]},
                {"$setOnInsert": video_doc},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error("Failed to insert video: %s", e)
            return False

    # ------------------------------------------------------------------
    # VET CLINIC METHODS
    # ------------------------------------------------------------------

    def get_clinics_by_region(self, region):
        return list(self._clinics.find({"region": region.lower()}))

    def get_all_clinics(self):
        return list(self._clinics.find({}))

    def insert_clinic(self, clinic_doc):
        try:
            self._clinics.update_one(
                {"clinic_id": clinic_doc["clinic_id"]},
                {"$setOnInsert": clinic_doc},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error("Failed to insert clinic: %s", e)
            return False

    # ------------------------------------------------------------------
    # REGIONAL ALERT METHODS
    # ------------------------------------------------------------------

    def get_alerts_by_region(self, region):
        return list(self._alerts.find({"target_region": region.lower()}))

    def insert_alert(self, alert_doc):
        try:
            self._alerts.insert_one(alert_doc)
            return True
        except Exception as e:
            logger.error("Failed to insert alert: %s", e)
            return False

    # ------------------------------------------------------------------
    # APPROVAL REQUEST METHODS
    # ------------------------------------------------------------------

    def get_all_approval_requests(self):
        return list(self._approvals.find({}))

    def get_pending_approval_requests(self):
        return list(self._approvals.find({"status": "Pending"}))

    def insert_approval_request(self, request_doc):
        try:
            self._approvals.insert_one(request_doc)
            return True
        except Exception as e:
            logger.error("Failed to insert approval request: %s", e)
            return False

    def update_approval_request_status(self, request_id, status):
        try:
            self._approvals.update_one(
                {"request_id": request_id},
                {"$set": {"status": status}}
            )
            return True
        except Exception as e:
            logger.error("Failed to update approval request: %s", e)
            return False

    # ------------------------------------------------------------------
    # SEED DATA
    # ------------------------------------------------------------------

    def seed_data(self):
        """Populate MongoDB with initial prototype data. Idempotent."""
        logger.info("Running seed_data()...")
        self._seed_guides()
        self._seed_videos()
        self._seed_clinics()
        logger.info("seed_data() complete.")

    def _seed_guides(self):
        guides = [
            {
                "guide_id": "G001",
                "emergency_category": "breathing",
                "step_by_step_instruction": [
                    "Keep the pet calm and limit movement.",
                    "Move the pet to a cool, well-ventilated area.",
                    "Check whether anything is blocking the airway.",
                    "Contact a veterinarian immediately.",
                ],
                "critical_warnings": [
                    "Do not force food or water.",
                    "Do not delay professional help if breathing difficulty continues.",
                ],
                "instructional_videos": [],
            },
            {
                "guide_id": "G002",
                "emergency_category": "bleeding",
                "step_by_step_instruction": [
                    "Apply gentle pressure to the wound with a clean cloth.",
                    "Keep the pet still to reduce further injury.",
                    "Wrap the area lightly if possible.",
                    "Seek veterinary assistance if bleeding does not stop.",
                ],
                "critical_warnings": [
                    "Do not remove deeply embedded objects.",
                    "Do not apply a tight tourniquet unless instructed by a vet.",
                ],
                "instructional_videos": [],
            },
            {
                "guide_id": "G003",
                "emergency_category": "vomiting",
                "step_by_step_instruction": [
                    "Remove food temporarily and observe the pet closely.",
                    "Offer small amounts of clean water if the pet can drink safely.",
                    "Check for repeated vomiting, weakness, or blood.",
                    "Contact a veterinarian if symptoms continue or worsen.",
                ],
                "critical_warnings": [
                    "Do not give human medication.",
                    "Seek urgent help if vomiting includes blood or severe weakness.",
                ],
                "instructional_videos": [],
            },
            {
                "guide_id": "G004",
                "emergency_category": "limping",
                "step_by_step_instruction": [
                    "Limit the pet's movement.",
                    "Check the paw or limb for visible injury.",
                    "Avoid forcing the pet to walk.",
                    "Arrange a vet check if limping persists.",
                ],
                "critical_warnings": [
                    "Do not pull or twist the injured limb.",
                    "Do not give painkillers unless prescribed by a vet.",
                ],
                "instructional_videos": [],
            },
            {
                "guide_id": "G005",
                "emergency_category": "itching",
                "step_by_step_instruction": [
                    "Prevent the pet from scratching or biting the affected area.",
                    "Check for visible signs of fleas, rashes, or swelling.",
                    "Rinse the area with cool clean water if irritation is localised.",
                    "Consult a vet if itching is severe or persistent.",
                ],
                "critical_warnings": [
                    "Do not apply human antihistamine creams without vet guidance.",
                    "Seek urgent care if swelling or hives are present.",
                ],
                "instructional_videos": [],
            },
        ]

        for guide in guides:
            self.insert_guide(guide)

    def _seed_videos(self):
        videos = [
            {
                "video_id": "V001",
                "title": "Helping a Pet With Breathing Difficulty",
                "youtube_url": "https://youtu.be/MVndPT9seFE",
                "duration": "4:20",
                "animal_tag": "Cat",
                "guide_id": "G001",
            },
            {
                "video_id": "V002",
                "title": "Basic Pet Wound Care",
                "youtube_url": "https://www.youtube.com/watch?v=MVndPT9seFE",
                "duration": "3:45",
                "animal_tag": "Dog",
                "guide_id": "G002",
            },
        ]
        for video in videos:
            self.insert_video(video)

    def _seed_clinics(self):
        clinics = [
            {
                "clinic_id": "C001",
                "clinic_name": "Happy Paws Veterinary Clinic",
                "region": "kuching",
                "operating_hours": "9:00 AM - 6:00 PM",
                "opening_hour": 9,
                "closing_hour": 18,
                "google_maps_link": "https://maps.google.com",
            },
            {
                "clinic_id": "C002",
                "clinic_name": "Emergency Animal Care Centre",
                "region": "miri",
                "operating_hours": "Open 24 hours",
                "opening_hour": 0,
                "closing_hour": 24,
                "google_maps_link": "https://maps.google.com",
            },
            {
                "clinic_id": "C003",
                "clinic_name": "Sarawak Animal Hospital",
                "region": "kuching",
                "operating_hours": "8:00 AM - 8:00 PM",
                "opening_hour": 8,
                "closing_hour": 20,
                "google_maps_link": "https://maps.google.com",
            },
        ]
        for clinic in clinics:
            self.insert_clinic(clinic)

    def close_connection(self):
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed.")
