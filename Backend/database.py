"""
database.py — Data Access Layer 
Pet First-Aid Web Application

This module is the **sole** file permitted to import ``pymongo``.
It implements a Singleton ``Database`` class that acts as the exclusive
gateway to the MongoDB instance.  All collection access, query execution,
and atomic write operations are centralised here to enforce a single
connection pool and prevent race conditions.

"""

import logging
from datetime import datetime, timezone
import re

import pymongo
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
MONGO_URI            = "mongodb://localhost:27017/"
DATABASE_NAME        = "pet_first_aid_db"
    
COLLECTION_USERS           = "Users"
COLLECTION_PET_PROFILES    = "PetProfiles"
COLLECTION_SYMPTOM_RECORDS = "SymptomRecords"
COLLECTION_FIRST_AID       = "FirstAidGuides"
COLLECTION_VIDEOS          = "InstructionalVideos"
COLLECTION_VET_DETAILS     = "VetDetails"
COLLECTION_ALERTS          = "RegionalAlerts"
COLLECTION_APPROVALS       = "ApprovalRequests"
COLLECTION_QUIZZES         = "EducationalQuizzes"

ROLE_PET_OWNER          = "pet_owner"
ROLE_ASSOCIATION_STAFF  = "association_staff"
ROLE_VET_PARTNER        = "veterinary_partner"

URGENCY_EMERGENCY    = "EMERGENCY"
URGENCY_URGENT       = "URGENT"
URGENCY_NON_URGENT   = "NON_URGENT"

STATUS_PENDING   = "pending"
STATUS_APPROVED  = "approved"
STATUS_REJECTED  = "rejected"

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Singleton Database class
# ---------------------------------------------------------------------------

class Database:
    """
    Singleton Data Access Layer wrapping a single ``pymongo`` ``MongoClient``.

    Only one instance is ever created per interpreter session (enforced via
    ``__new__``).  All callers obtain the same connection pool, preventing
    redundant connections to MongoDB.

    Usage
    -----
    ::

        db = Database()
        user = db.findUserByEmail("owner@example.com")

    Notes
    -----
    * No other module may import ``pymongo`` directly.
    * All write methods that modify shared counters or state-fields use atomic
      MongoDB operators to guarantee consistency under concurrent requests.
    """

    _instance = None   # Holds the single shared instance

    # ------------------------------------------------------------------
    # Singleton enforcement
    # ------------------------------------------------------------------

    def __new__(cls):
        """
        Override ``__new__`` to enforce the Singleton pattern.

        If an instance already exists it is returned unchanged; otherwise a
        new instance is created, the MongoDB client is initialised, and all
        required collection indexes are created.

        Returns
        -------
        Database
            The single shared ``Database`` instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialise()
        return cls._instance

    # ------------------------------------------------------------------
    # Initialisation (called once by __new__)
    # ------------------------------------------------------------------

    def _initialise(self):
        """
        Establish the MongoDB connection and obtain collection handles.

        Called exactly once when the Singleton is first constructed.
        Also triggers index creation to enforce uniqueness constraints
        and optimise common query paths.
        """
        self._client = MongoClient(MONGO_URI)
        self._db     = self._client[DATABASE_NAME]

        # Collection handles
        self._users          = self._db[COLLECTION_USERS]
        self._petProfiles    = self._db[COLLECTION_PET_PROFILES]
        self._symptomRecords = self._db[COLLECTION_SYMPTOM_RECORDS]
        self._firstAid       = self._db[COLLECTION_FIRST_AID]
        self._videos         = self._db[COLLECTION_VIDEOS]
        self._vetDetails     = self._db[COLLECTION_VET_DETAILS]
        self._alerts         = self._db[COLLECTION_ALERTS]
        self._approvals      = self._db[COLLECTION_APPROVALS]
        self._quizzes        = self._db[COLLECTION_QUIZZES]

        self._createIndexes()
        logger.info("Database Singleton initialised — connected to '%s'.", DATABASE_NAME)

    def _createIndexes(self):
        """
        Create all collection indexes on first run (idempotent).

        Unique indexes prevent duplicate registrations; compound indexes
        accelerate the most common query patterns used by the service layer.
        """
        # Users — unique email across all roles
        self._users.create_index(
            [("email", ASCENDING)], unique=True, name="idx_users_email"
        )

        # PetProfiles — owner lookup
        self._petProfiles.create_index(
            [("ownerId", ASCENDING)], name="idx_petprofiles_owner"
        )

        # FirstAidGuides — species + keyword search
        self._firstAid.create_index(
            [("species", ASCENDING), ("keywords", ASCENDING)],
            name="idx_firstaid_species_keywords"
        )

        # Videos — species lookup
        self._videos.create_index(
            [("species", ASCENDING)], name="idx_videos_species"
        )

        # RegionalAlerts — region + active flag
        self._alerts.create_index(
            [("region", ASCENDING), ("isActive", ASCENDING)],
            name="idx_alerts_region_active"
        )

        # ApprovalRequests — status queue
        self._approvals.create_index(
            [("status", ASCENDING), ("submittedAt", DESCENDING)],
            name="idx_approvals_status_date"
        )

        # SymptomRecords — pet lookup
        self._symptomRecords.create_index(
            [("petId", ASCENDING)], name="idx_symptoms_pet"
        )

        # EducationalQuizzes — topic
        self._quizzes.create_index(
            [("topic", ASCENDING)], name="idx_quizzes_topic"
        )

        logger.debug("MongoDB indexes verified/created.")

    # ==================================================================
    # USER COLLECTION METHODS
    # ==================================================================

    def insertUser(self, userDocument: dict) -> str:
        """
        Insert a new user document into the ``Users`` collection.

        Parameters
        ----------
        userDocument : dict
            A fully-formed user document (role, email, passwordHash, etc.).

        Returns
        -------
        str
            The ``_id`` string of the newly inserted document.

        Raises
        ------
        DuplicateKeyError
            If a user with the same email already exists.
        PyMongoError
            On any other database error.
        """
        userDocument["createdAt"] = datetime.now(timezone.utc)
        result = self._users.insert_one(userDocument)
        return str(result.inserted_id)

    def findUserByEmail(self, email: str) -> dict | None:
        """
        Retrieve a single user document by email address (case-insensitive).

        Parameters
        ----------
        email : str
            The email address to search for.

        Returns
        -------
        dict or None
            The matching user document, or ``None`` if not found.
        """
        return self._users.find_one({"email": email.strip().lower()})

    def findUserById(self, userId: str) -> dict | None:
        """
        Retrieve a single user document by its ``_id``.

        Parameters
        ----------
        userId : str
            Hex string representation of the MongoDB ``ObjectId``.

        Returns
        -------
        dict or None
            The matching user document, or ``None`` if not found.
        """
        try:
            return self._users.find_one({"_id": ObjectId(userId)})
        except Exception:
            return None

    def updateUserProfile(self, userId: str, updateFields: dict) -> dict | None:
        """
        Atomically update specified fields on a user document.

        Uses ``find_one_and_update`` with ``return_document=True`` so the
        caller always receives the post-update state, avoiding a separate
        read after write.

        Parameters
        ----------
        userId : str
            Target user's ``_id`` as a hex string.
        updateFields : dict
            Key-value pairs to set via the ``$set`` operator.

        Returns
        -------
        dict or None
            The updated user document, or ``None`` if not found.
        """
        updateFields["updatedAt"] = datetime.now(timezone.utc)
        return self._users.find_one_and_update(
            {"_id": ObjectId(userId)},
            {"$set": updateFields},
            return_document=pymongo.ReturnDocument.AFTER
        )

    def findUsersByRole(self, role: str) -> list[dict]:
        """
        Retrieve all users with a given role.

        Parameters
        ----------
        role : str
            One of the ``ROLE_*`` constants defined in this module.

        Returns
        -------
        list[dict]
            List of matching user documents (may be empty).
        """
        return list(self._users.find({"role": role}))

    # ==================================================================
    # PET PROFILE COLLECTION METHODS
    # ==================================================================

    def insertPetProfile(self, profileDocument: dict) -> str:
        """
        Insert a new pet profile document.

        Parameters
        ----------
        profileDocument : dict
            Pet profile data including ``ownerId``, ``name``, ``species``,
            ``breed``, ``age``, ``weight``, and ``medicalHistory``.

        Returns
        -------
        str
            The ``_id`` of the newly inserted document.
        """
        profileDocument["createdAt"] = datetime.now(timezone.utc)
        result = self._petProfiles.insert_one(profileDocument)
        return str(result.inserted_id)

    def findPetsByOwner(self, ownerId: str) -> list[dict]:
        """
        Retrieve all pet profiles belonging to a specific owner.

        Parameters
        ----------
        ownerId : str
            The owner's user ``_id`` as a hex string.

        Returns
        -------
        list[dict]
            List of pet profile documents.
        """
        return list(self._petProfiles.find({"ownerId": ownerId}))

    def findPetById(self, petId: str) -> dict | None:
        """
        Retrieve a single pet profile by its ``_id``.

        Parameters
        ----------
        petId : str
            Hex string of the pet's ``ObjectId``.

        Returns
        -------
        dict or None
        """
        try:
            return self._petProfiles.find_one({"_id": ObjectId(petId)})
        except Exception:
            return None

    def updatePetProfile(self, petId: str, updateFields: dict) -> dict | None:
        """
        Atomically update a pet profile document.

        Parameters
        ----------
        petId : str
            Target pet's ``_id`` as a hex string.
        updateFields : dict
            Fields to update via ``$set``.

        Returns
        -------
        dict or None
            The updated pet profile document.
        """
        updateFields["updatedAt"] = datetime.now(timezone.utc)
        return self._petProfiles.find_one_and_update(
            {"_id": ObjectId(petId)},
            {"$set": updateFields},
            return_document=pymongo.ReturnDocument.AFTER
        )

    def deletePetProfile(self, petId: str) -> bool:
        """
        Delete a pet profile document by ``_id``.

        Parameters
        ----------
        petId : str
            Hex string of the pet's ``ObjectId``.

        Returns
        -------
        bool
            ``True`` if a document was deleted, ``False`` otherwise.
        """
        result = self._petProfiles.delete_one({"_id": ObjectId(petId)})
        return result.deleted_count > 0

    # ==================================================================
    # SYMPTOM RECORD COLLECTION METHODS
    # ==================================================================

    def insertSymptomRecord(self, symptomDocument: dict) -> str:
        """
        Persist a triage symptom record for a pet.

        Parameters
        ----------
        symptomDocument : dict
            Includes ``petId``, ``symptoms`` list, ``urgencyLevel``,
            ``triageNotes``, and ``assessedAt`` timestamp.

        Returns
        -------
        str
            The ``_id`` of the inserted record.
        """
        symptomDocument["assessedAt"] = datetime.now(timezone.utc)
        result = self._symptomRecords.insert_one(symptomDocument)
        return str(result.inserted_id)

    def findSymptomsByPet(self, petId: str) -> list[dict]:
        """
        Retrieve all triage records for a specific pet, most recent first.

        Parameters
        ----------
        petId : str
            The pet's ``_id`` as a hex string.

        Returns
        -------
        list[dict]
            Symptom record documents sorted by ``assessedAt`` descending.
        """
        return list(
            self._symptomRecords.find(
                {"petId": petId}
            ).sort("assessedAt", DESCENDING)
        )

    # ==================================================================
    # FIRST AID GUIDE COLLECTION METHODS
    # ==================================================================

    def insertFirstAidGuide(self, guideDocument: dict) -> str:
        """
        Insert a new first aid guide document.

        Parameters
        ----------
        guideDocument : dict
            Includes ``title``, ``species``, ``keywords``, ``steps``,
            ``urgencyLevel``, and ``approvedBy``.

        Returns
        -------
        str
            The ``_id`` of the inserted guide.
        """
        guideDocument["createdAt"] = datetime.now(timezone.utc)
        result = self._firstAid.insert_one(guideDocument)
        return str(result.inserted_id)

    def searchFirstAidGuides(self, species: str, keywords: list[str]) -> list[dict]:
        """
        Search for first aid guides matching a species and keyword list.

        Parameters
        ----------
        species : str
            Target animal species (e.g. ``"dog"``, ``"cat"``).
        keywords : list[str]
            List of symptom or condition keywords to match against.

        Returns
        -------
        list[dict]
            Matching guide documents.
        """
        query = {
            "species": species.lower(),
            "keywords": {"$in": [kw.lower() for kw in keywords]}
        }
        return list(self._firstAid.find(query))

    def findAllFirstAidGuides(self) -> list[dict]:
        """
        Retrieve all first aid guides from the collection.

        Returns
        -------
        list[dict]
        """
        return list(self._firstAid.find({}))

    def findFirstAidGuideById(self, guideId: str) -> dict | None:
        """
        Retrieve a single first aid guide by ``_id``.

        Parameters
        ----------
        guideId : str

        Returns
        -------
        dict or None
        """
        try:
            return self._firstAid.find_one({"_id": ObjectId(guideId)})
        except Exception:
            return None

    def updateFirstAidGuide(self, guideId: str, updateFields: dict) -> dict | None:
        """
        Atomically update a first aid guide.

        Parameters
        ----------
        guideId : str
        updateFields : dict

        Returns
        -------
        dict or None
            The updated guide document.
        """
        updateFields["updatedAt"] = datetime.now(timezone.utc)
        return self._firstAid.find_one_and_update(
            {"_id": ObjectId(guideId)},
            {"$set": updateFields},
            return_document=pymongo.ReturnDocument.AFTER
        )

    # ==================================================================
    # INSTRUCTIONAL VIDEO COLLECTION METHODS
    # ==================================================================

    def insertVideo(self, videoDocument: dict) -> str:
        """
        Insert a new instructional video document.

        Parameters
        ----------
        videoDocument : dict
            Includes ``title``, ``species``, ``url``, ``durationSeconds``,
            ``description``, and ``uploadedBy``.

        Returns
        -------
        str
            The ``_id`` of the inserted video.
        """
        videoDocument["uploadedAt"] = datetime.now(timezone.utc)
        result = self._videos.insert_one(videoDocument)
        return str(result.inserted_id)

    def findVideosBySpecies(self, species: str) -> list[dict]:
        """
        Retrieve all approved instructional videos for a given species.

        Parameters
        ----------
        species : str

        Returns
        -------
        list[dict]
        """
        return list(self._videos.find({"species": species.lower(), "isApproved": True}))

    def findAllVideos(self) -> list[dict]:
        """
        Retrieve all video documents regardless of approval status.

        Returns
        -------
        list[dict]
        """
        return list(self._videos.find({}))

    def incrementVideoViewCount(self, videoId: str) -> dict | None:
        """
        Atomically increment the ``viewCount`` of a video by 1.

        Uses ``$inc`` to avoid read-modify-write race conditions in a
        concurrent request environment.

        Parameters
        ----------
        videoId : str

        Returns
        -------
        dict or None
            The updated video document.
        """
        return self._videos.find_one_and_update(
            {"_id": ObjectId(videoId)},
            {"$inc": {"viewCount": 1}},
            return_document=pymongo.ReturnDocument.AFTER
        )

    # ==================================================================
    # VET DETAILS COLLECTION METHODS
    # ==================================================================

    def insertVetDetails(self, vetDocument: dict) -> str:
        """
        Insert a veterinary clinic directory record.

        Parameters
        ----------
        vetDocument : dict
            Includes clinicName, licenseNumber, specialisations, region,
            contactInfo, operatingHours, and createdByStaffId.
        """
        vetDocument["createdAt"] = datetime.now(timezone.utc)
        result = self._vetDetails.insert_one(vetDocument)
        return str(result.inserted_id)

    def findVetsByRegion(self, region: str) -> list[dict]:
        """
        Retrieve all active vets in a given region.

        Parameters
        ----------
        region : str

        Returns
        -------
        list[dict]
        """
        regionPattern = f"^{re.escape(region.strip())}$"
        return list(self._vetDetails.find({
            "region": {"$regex": regionPattern, "$options": "i"},
            "isActive": True,
        }))

    # ==================================================================
    # REGIONAL ALERT COLLECTION METHODS
    # ==================================================================

    def insertAlert(self, alertDocument: dict) -> str:
        """
        Insert a new regional alert document.

        Parameters
        ----------
        alertDocument : dict
            Includes ``title``, ``description``, ``region``, ``severity``,
            ``isActive``, and ``createdBy``.

        Returns
        -------
        str
            The ``_id`` of the inserted alert.
        """
        alertDocument["createdAt"] = datetime.now(timezone.utc)
        alertDocument["isActive"]  = alertDocument.get("isActive", True)
        result = self._alerts.insert_one(alertDocument)
        return str(result.inserted_id)

    def findActiveAlertsByRegion(self, region: str) -> list[dict]:
        """
        Retrieve all currently active alerts for a given region.

        Parameters
        ----------
        region : str

        Returns
        -------
        list[dict]
        """
        regionPattern = f"^{re.escape(region.strip())}$"
        return list(self._alerts.find({
            "region": {"$regex": regionPattern, "$options": "i"},
            "isActive": True,
        }))

    def findAllAlerts(self) -> list[dict]:
        """
        Retrieve every regional alert regardless of status.

        Returns
        -------
        list[dict]
        """
        return list(self._alerts.find({}))

    def deactivateAlert(self, alertId: str) -> dict | None:
        """
        Atomically set an alert's ``isActive`` flag to ``False``.

        Parameters
        ----------
        alertId : str

        Returns
        -------
        dict or None
            The updated alert document.
        """
        return self._alerts.find_one_and_update(
            {"_id": ObjectId(alertId)},
            {"$set": {"isActive": False, "deactivatedAt": datetime.now(timezone.utc)}},
            return_document=pymongo.ReturnDocument.AFTER
        )

    # ==================================================================
    # APPROVAL REQUEST COLLECTION METHODS
    # ==================================================================

    def insertApprovalRequest(self, requestDocument: dict) -> str:
        """
        Insert a new content approval request submitted by a vet partner.

        Parameters
        ----------
        requestDocument : dict
            Includes ``submittedBy``, ``contentType``, ``contentData``,
            and ``status`` (defaults to ``pending``).

        Returns
        -------
        str
            The ``_id`` of the inserted request.
        """
        requestDocument["submittedAt"] = datetime.now(timezone.utc)
        requestDocument["status"]      = STATUS_PENDING
        result = self._approvals.insert_one(requestDocument)
        return str(result.inserted_id)

    def findApprovalRequestsByStatus(self, status: str) -> list[dict]:
        """
        Retrieve all approval requests with a given status.

        Parameters
        ----------
        status : str
            One of ``STATUS_PENDING``, ``STATUS_APPROVED``, or
            ``STATUS_REJECTED``.

        Returns
        -------
        list[dict]
        """
        return list(
            self._approvals.find({"status": status}).sort("submittedAt", DESCENDING)
        )

    def updateApprovalStatus(
        self, requestId: str, status: str, reviewedBy: str, reviewNotes: str = ""
    ) -> dict | None:
        """
        Atomically update the status of an approval request.

        Uses ``find_one_and_update`` to atomically transition the status
        field, preventing duplicate approvals or rejections under concurrent
        moderator sessions.

        Parameters
        ----------
        requestId : str
        status : str
            New status value (``approved`` or ``rejected``).
        reviewedBy : str
            ``_id`` of the ``AssociationStaff`` reviewer.
        reviewNotes : str, optional
            Moderator notes appended to the record.

        Returns
        -------
        dict or None
            The updated approval request document.
        """
        return self._approvals.find_one_and_update(
            {"_id": ObjectId(requestId), "status": STATUS_PENDING},
            {
                "$set": {
                    "status":      status,
                    "reviewedBy":  reviewedBy,
                    "reviewNotes": reviewNotes,
                    "reviewedAt":  datetime.now(timezone.utc),
                }
            },
            return_document=pymongo.ReturnDocument.AFTER
        )

    def findApprovalRequestById(self, requestId: str) -> dict | None:
        """
        Retrieve a single approval request by ``_id``.

        Parameters
        ----------
        requestId : str

        Returns
        -------
        dict or None
        """
        try:
            return self._approvals.find_one({"_id": ObjectId(requestId)})
        except Exception:
            return None

    # ==================================================================
    # EDUCATIONAL QUIZ COLLECTION METHODS
    # ==================================================================

    def insertQuiz(self, quizDocument: dict) -> str:
        """
        Insert a new educational quiz document.

        Parameters
        ----------
        quizDocument : dict
            Includes ``title``, ``topic``, ``questions`` (embedded list),
            ``createdBy``, and ``difficultyLevel``.

        Returns
        -------
        str
            The ``_id`` of the inserted quiz.
        """
        quizDocument["createdAt"] = datetime.now(timezone.utc)
        result = self._quizzes.insert_one(quizDocument)
        return str(result.inserted_id)

    def findQuizzesByTopic(self, topic: str) -> list[dict]:
        """
        Retrieve all quizzes matching a given topic.

        Parameters
        ----------
        topic : str

        Returns
        -------
        list[dict]
        """
        return list(self._quizzes.find({"topic": topic}))

    def findAllQuizzes(self) -> list[dict]:
        """
        Retrieve all quiz documents.

        Returns
        -------
        list[dict]
        """
        return list(self._quizzes.find({}))

    def findQuizById(self, quizId: str) -> dict | None:
        """
        Retrieve a single quiz by ``_id``.

        Parameters
        ----------
        quizId : str

        Returns
        -------
        dict or None
        """
        try:
            return self._quizzes.find_one({"_id": ObjectId(quizId)})
        except Exception:
            return None

    # ==================================================================
    # SEED DATA
    # ==================================================================

    def seed_data(self):
        """
        Populate the database with initial prototype data.

        Inserts a default ``AssociationStaff`` admin account, two sample
        ``VeterinaryPartner`` accounts, a ``PetOwner``, sample pet profiles,
        first aid guides, instructional videos, a regional alert, and an
        educational quiz.

        This method is **idempotent**: it checks for existing documents
        before inserting and skips duplicates gracefully.

        Intended for development/prototype use only.
        """
        logger.info("Running seed_data()…")

        # ------------------------------------------------------------------
        # 1. USERS
        # ------------------------------------------------------------------
        seed_users = [
            {
                "email":        "admin@petfirstaid.org",
                "passwordHash": "hashed_admin_password_placeholder",
                "role":         ROLE_ASSOCIATION_STAFF,
                "fullName":     "Alice Admin",
                "staffId":      "STAFF-001",
                "department":   "Content Management",
                "permissions":  ["approve_content", "manage_alerts", "manage_users"],
                "isActive":     True,
            },
            {
                "email":        "dr.tan@vetclinic.com",
                "passwordHash": "hashed_vet1_password_placeholder",
                "role":         ROLE_VET_PARTNER,
                "fullName":     "Dr. Tan Wei Ming",
                "licenseNumber":"VET-MY-00123",
                "specialisations": ["small animals", "emergency care"],
                "isVerified":   True,
                "isActive":     True,
            },
            {
                "email":        "dr.siti@animalhospital.com",
                "passwordHash": "hashed_vet2_password_placeholder",
                "role":         ROLE_VET_PARTNER,
                "fullName":     "Dr. Siti Nurhaliza",
                "licenseNumber":"VET-MY-00456",
                "specialisations": ["exotic animals", "feline care"],
                "isVerified":   True,
                "isActive":     True,
            },
            {
                "email":        "owner@example.com",
                "passwordHash": "hashed_owner_password_placeholder",
                "role":         ROLE_PET_OWNER,
                "fullName":     "John Lim",
                "phoneNumber":  "+60123456789",
                "region":       "Kuching",
                "isActive":     True,
            },
        ]

        inserted_user_ids = {}
        for user in seed_users:
            existing = self._users.find_one({"email": user["email"]})
            if not existing:
                uid = self.insertUser(user)
                inserted_user_ids[user["email"]] = uid
                logger.info("Seeded user: %s", user["email"])
            else:
                inserted_user_ids[user["email"]] = str(existing["_id"])
                logger.debug("User already exists, skipping: %s", user["email"])

        owner_id = inserted_user_ids.get("owner@example.com")
        staff_id = inserted_user_ids.get("admin@petfirstaid.org")
        vet1_id  = inserted_user_ids.get("dr.tan@vetclinic.com")

        # ------------------------------------------------------------------
        # 2. VET DETAILS
        # ------------------------------------------------------------------
        self._vetDetails.delete_many({
            "$or": [
                {"clinicName": "PetCare Veterinary Clinic"},
                {"region": {"$regex": "Kuala Lumpur|KL|Klang Valley", "$options": "i"}},
                {"contactInfo.address": {"$regex": "Kuala Lumpur|KL|Klang Valley", "$options": "i"}},
            ]
        })

        sarawakVets = [
            {
                "clinicName": "Animal Central Veterinary Sdn Bhd",
                "licenseNumber": "SAR-KCH-001",
                "specialisations": ["small animals", "emergency care"],
                "region": "Kuching",
                "contactInfo": {
                    "phone": "016-9377234",
                    "address": "Lot 70 Jalan Tabuan, 93100 Kuching, Sarawak",
                    "email": "",
                    "mapsLink": "https://maps.app.goo.gl/d5TJ1Rh26ynQcnuRA",
                },
                "operatingHours": "24 hours",
                "createdByStaffId": staff_id,
                "isActive": True,
            },
            {
                "clinicName": "Anypets Veterinary Clinic",
                "licenseNumber": "SAR-KCH-002",
                "specialisations": ["small animals", "general practice"],
                "region": "Kuching",
                "contactInfo": {
                    "phone": "010-2557789",
                    "address": "No. 45, Ground Floor Lot 20145, Block 11, Milan Square, Jalan Wan Alwi, 93350 Kuching, Sarawak",
                    "email": "",
                    "mapsLink": "https://maps.app.goo.gl/3gcTnJYjRGyQ2oDv9",
                },
                "operatingHours": "8:00 AM - 8:00 PM",
                "createdByStaffId": staff_id,
                "isActive": True,
            },
            {
                "clinicName": "Bettie Veterinary Clinic and Surgery",
                "licenseNumber": "SAR-MYY-001",
                "specialisations": ["small animals", "surgery"],
                "region": "Miri",
                "contactInfo": {
                    "phone": "085-439439",
                    "address": "Lot 1490-1492, Jalan Krokop, 98000 Miri, Sarawak",
                    "email": "",
                    "mapsLink": "https://www.google.com/maps/search/?api=1&query=Bettie+Veterinary+Clinic+and+Surgery+Miri",
                },
                "operatingHours": "24 hours",
                "createdByStaffId": staff_id,
                "isActive": True,
            },
            {
                "clinicName": "J&J Animal Clinic",
                "licenseNumber": "SAR-MYY-002",
                "specialisations": ["small animals", "general practice"],
                "region": "Miri",
                "contactInfo": {
                    "phone": "010-9820661",
                    "address": "Lot 2062, Jalan MS1/6, Marina Square 1, Marina Parkcity, 98000 Miri, Sarawak",
                    "email": "",
                    "mapsLink": "https://www.google.com/maps/search/?api=1&query=J%26J+Animal+Clinic+Miri",
                },
                "operatingHours": "Contact clinic to confirm operating hours",
                "createdByStaffId": staff_id,
                "isActive": True,
            },
            {
                "clinicName": "Alliance Veterinary Clinic",
                "licenseNumber": "SAR-BTU-001",
                "specialisations": ["small animals", "general practice"],
                "region": "Bintulu",
                "contactInfo": {
                    "phone": "086-316339",
                    "address": "Shophouse 69, Ground Floor, Jalan Tun Hussein Onn, Taman Tinggi, 97000 Bintulu, Sarawak",
                    "email": "",
                    "mapsLink": "https://www.google.com/maps/search/?api=1&query=Alliance+Veterinary+Clinic+Bintulu",
                },
                "operatingHours": "8:00 AM - 8:00 PM",
                "createdByStaffId": staff_id,
                "isActive": True,
            },
            {
                "clinicName": "Cheng Animal Clinic & Surgery",
                "licenseNumber": "SAR-BTU-002",
                "specialisations": ["small animals", "surgery"],
                "region": "Bintulu",
                "contactInfo": {
                    "phone": "011-125158613",
                    "address": "SL253, Lot 946, Jalan Tanjong Batu, Kemena Commercial Centre, 97000 Bintulu, Sarawak",
                    "email": "",
                    "mapsLink": "https://www.google.com/maps/search/?api=1&query=Cheng+Animal+Clinic+and+Surgery+Bintulu",
                },
                "operatingHours": "Contact clinic to confirm operating hours",
                "createdByStaffId": staff_id,
                "isActive": True,
            },
            {
                "clinicName": "Central Veterinary Clinic",
                "licenseNumber": "SAR-SBW-001",
                "specialisations": ["small animals", "general practice"],
                "region": "Sibu",
                "contactInfo": {
                    "phone": "084-333339",
                    "address": "No. 14, Ground Floor, Jalan Merdeka Barat, 96000 Sibu, Sarawak",
                    "email": "",
                    "mapsLink": "https://www.google.com/maps/search/?api=1&query=Central+Veterinary+Clinic+Sibu",
                },
                "operatingHours": "8:00 AM - 8:00 PM",
                "createdByStaffId": staff_id,
                "isActive": True,
            },
            {
                "clinicName": "Pawsitive Vet Clinic",
                "licenseNumber": "SAR-SBW-002",
                "specialisations": ["small animals", "general practice"],
                "region": "Sibu",
                "contactInfo": {
                    "phone": "084-311868",
                    "address": "No. 104, Ground Floor, Lorong 4, Jalan Sungai Merah, 96000 Sibu, Sarawak",
                    "email": "",
                    "mapsLink": "https://www.google.com/maps/search/?api=1&query=Pawsitive+Vet+Clinic+Sibu",
                },
                "operatingHours": "24 hours",
                "createdByStaffId": staff_id,
                "isActive": True,
            },
        ]

        for vet in sarawakVets:
            if not self._vetDetails.find_one({"clinicName": vet["clinicName"]}):
                self.insertVetDetails(vet)
            else:
                self._vetDetails.update_one(
                    {"clinicName": vet["clinicName"]},
                    {"$set": vet},
                )

        # ------------------------------------------------------------------
        # 3. PET PROFILES
        # ------------------------------------------------------------------
        if owner_id and not self._petProfiles.find_one({"ownerId": owner_id}):
            self.insertPetProfile({
                "ownerId":       owner_id,
                "name":          "Buddy",
                "species":       "dog",
                "breed":         "Golden Retriever",
                "age":           3,
                "weightKg":      28.5,
                "sex":           "male",
                "isNeutered":    True,
                "medicalHistory": ["annual vaccinations up to date", "no known allergies"],
                "emergencyNotes": "",
            })
            self.insertPetProfile({
                "ownerId":       owner_id,
                "name":          "Whiskers",
                "species":       "cat",
                "breed":         "Domestic Shorthair",
                "age":           5,
                "weightKg":      4.2,
                "sex":           "female",
                "isNeutered":    True,
                "medicalHistory": ["hyperthyroidism — on medication"],
                "emergencyNotes": "Sensitive to stress; handle calmly.",
            })
            logger.info("Seeded pet profiles for owner.")

        # ------------------------------------------------------------------
        # 4. FIRST AID GUIDES
        # ------------------------------------------------------------------
        obsoleteGuideTitles = [
            "Choking in Dogs",
            "Heatstroke in Dogs",
            "Minor Wound Care for Cats",
            "Seizures in Dogs",
        ]
        self._firstAid.delete_many({"title": {"$in": obsoleteGuideTitles}})

        guides = [
            {
                "title":        "Breathing Difficulty in Dogs",
                "species":      "dog",
                "urgencyLevel": URGENCY_EMERGENCY,
                "keywords":     ["breathing", "breathing difficulty", "wheezing", "shortness of breath"],
                "steps": [
                    "Keep the dog calm and limit movement.",
                    "Move the dog to a cool, well-ventilated area.",
                    "Check for visible airway blockage without forcing the mouth open.",
                    "Contact an emergency veterinarian immediately.",
                ],
                "warningNotes": "Do not force food, water, or medication. Breathing difficulty is an emergency.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Breathing Difficulty in Cats",
                "species":      "cat",
                "urgencyLevel": URGENCY_EMERGENCY,
                "keywords":     ["breathing", "breathing difficulty", "wheezing", "open mouth breathing"],
                "steps": [
                    "Keep the cat calm and avoid handling more than necessary.",
                    "Place the cat in a quiet, well-ventilated carrier.",
                    "Do not attempt home treatment for open-mouth breathing.",
                    "Transport to an emergency veterinarian immediately.",
                ],
                "warningNotes": "Open-mouth breathing in cats is always urgent and requires veterinary care.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Bleeding and Wound Care for Dogs",
                "species":      "dog",
                "urgencyLevel": URGENCY_URGENT,
                "keywords":     ["bleeding", "wound", "cut", "scratch", "laceration"],
                "steps": [
                    "Apply gentle pressure with a clean cloth or bandage.",
                    "Keep the dog still to reduce further bleeding.",
                    "Rinse minor dirt away with clean water if safe.",
                    "Seek veterinary care if bleeding continues or the wound is deep.",
                ],
                "warningNotes": "Do not remove deeply embedded objects and do not apply a tight tourniquet.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Bleeding and Wound Care for Cats",
                "species":      "cat",
                "urgencyLevel": URGENCY_URGENT,
                "keywords":     ["bleeding", "wound", "cut", "scratch", "laceration"],
                "steps": [
                    "Approach calmly and avoid sudden handling.",
                    "Apply gentle pressure with a clean cloth if the cat allows it.",
                    "Keep the cat indoors and limit movement.",
                    "Seek veterinary care if bleeding continues or the wound is deep.",
                ],
                "warningNotes": "Cat wounds can become infected quickly. Do not use human antiseptics.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Vomiting in Dogs",
                "species":      "dog",
                "urgencyLevel": URGENCY_URGENT,
                "keywords":     ["vomiting", "throwing up", "nausea", "retching"],
                "steps": [
                    "Remove food temporarily and observe the dog closely.",
                    "Offer small amounts of clean water if the dog can drink safely.",
                    "Check for repeated vomiting, weakness, bloating, or blood.",
                    "Contact a veterinarian if symptoms continue or worsen.",
                ],
                "warningNotes": "Seek urgent help if vomiting includes blood, severe weakness, or a swollen abdomen.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Vomiting in Cats",
                "species":      "cat",
                "urgencyLevel": URGENCY_URGENT,
                "keywords":     ["vomiting", "throwing up", "nausea", "retching"],
                "steps": [
                    "Remove food temporarily and monitor the cat closely.",
                    "Ensure clean water is available, but do not force drinking.",
                    "Check for repeated vomiting, lethargy, or blood.",
                    "Contact a veterinarian if vomiting repeats or the cat appears weak.",
                ],
                "warningNotes": "Repeated vomiting in cats can quickly lead to dehydration.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Limping in Dogs",
                "species":      "dog",
                "urgencyLevel": URGENCY_NON_URGENT,
                "keywords":     ["limping", "lameness", "leg pain", "paw injury"],
                "steps": [
                    "Limit the dog's movement and prevent running or jumping.",
                    "Check the paw for thorns, cuts, swelling, or trapped objects.",
                    "Apply a cold compress if swelling is visible.",
                    "Arrange a vet check if limping persists or the dog cannot bear weight.",
                ],
                "warningNotes": "Do not give human painkillers unless prescribed by a veterinarian.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Limping in Cats",
                "species":      "cat",
                "urgencyLevel": URGENCY_NON_URGENT,
                "keywords":     ["limping", "lameness", "leg pain", "paw injury"],
                "steps": [
                    "Keep the cat indoors and restrict climbing or jumping.",
                    "Check the paw gently for visible injury or swelling.",
                    "Place food, water, and litter nearby to reduce movement.",
                    "Arrange a vet check if limping continues or the cat hides in pain.",
                ],
                "warningNotes": "Cats often hide pain; persistent limping should be checked by a vet.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Itching and Skin Irritation in Dogs",
                "species":      "dog",
                "urgencyLevel": URGENCY_NON_URGENT,
                "keywords":     ["itching", "skin irritation", "rash", "scratching"],
                "steps": [
                    "Prevent excessive scratching or licking if possible.",
                    "Check the skin for redness, fleas, swelling, or discharge.",
                    "Rinse mild irritants away with clean water.",
                    "Schedule a vet check if irritation spreads or does not improve.",
                ],
                "warningNotes": "Do not apply human creams or medication unless advised by a veterinarian.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Itching and Skin Irritation in Cats",
                "species":      "cat",
                "urgencyLevel": URGENCY_NON_URGENT,
                "keywords":     ["itching", "skin irritation", "rash", "scratching"],
                "steps": [
                    "Prevent over-grooming if it is causing wounds.",
                    "Check for fleas, redness, scabs, or swelling.",
                    "Avoid bathing unless advised, as it may increase stress.",
                    "Schedule a vet check if irritation persists or wounds appear.",
                ],
                "warningNotes": "Do not use dog flea products or human skin products on cats.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
        ]

        smallPetSpeciesLabels = {
            "rabbit": "Rabbits",
            "hamster": "Hamsters",
            "guinea pig": "Guinea Pigs",
            "bird": "Birds",
            "tortoise": "Tortoises",
        }
        smallPetGuideTemplates = {
            "breathing": {
                "title": "Breathing Difficulty",
                "urgencyLevel": URGENCY_EMERGENCY,
                "keywords": ["breathing", "breathing difficulty", "wheezing", "shortness of breath"],
                "steps": [
                    "Keep the pet calm and limit handling.",
                    "Move the pet to a quiet, well-ventilated area.",
                    "Do not force food, water, or medication.",
                    "Contact an emergency veterinarian immediately.",
                ],
                "warningNotes": "Breathing difficulty in small pets can become serious very quickly.",
            },
            "bleeding": {
                "title": "Bleeding and Wound Care",
                "urgencyLevel": URGENCY_URGENT,
                "keywords": ["bleeding", "wound", "cut", "scratch", "injury"],
                "steps": [
                    "Approach gently and avoid sudden handling.",
                    "Apply light pressure with clean gauze or cloth if safe.",
                    "Keep the pet warm, quiet, and contained.",
                    "Contact a veterinarian if bleeding continues or the wound is deep.",
                ],
                "warningNotes": "Small pets can lose blood quickly. Do not use human antiseptics unless advised by a vet.",
            },
            "vomiting": {
                "title": "Vomiting or Digestive Upset",
                "urgencyLevel": URGENCY_URGENT,
                "keywords": ["vomiting", "digestive", "diarrhea", "not eating", "lethargy"],
                "steps": [
                    "Remove unsafe food and observe the pet closely.",
                    "Keep clean water available if the species can drink safely.",
                    "Check for repeated symptoms, weakness, or bloating.",
                    "Contact a veterinarian if symptoms continue or the pet becomes weak.",
                ],
                "warningNotes": "Digestive problems in small pets can worsen quickly and may require prompt veterinary care.",
            },
            "limping": {
                "title": "Limping or Movement Difficulty",
                "urgencyLevel": URGENCY_NON_URGENT,
                "keywords": ["limping", "lameness", "leg pain", "movement", "injury"],
                "steps": [
                    "Limit movement and keep the pet in a safe enclosure.",
                    "Check gently for visible swelling, cuts, or trapped objects.",
                    "Avoid pulling, twisting, or forcing the limb.",
                    "Arrange a vet check if limping continues or the pet cannot move normally.",
                ],
                "warningNotes": "Do not give pain medication unless prescribed by a veterinarian.",
            },
            "itching": {
                "title": "Itching and Skin Irritation",
                "urgencyLevel": URGENCY_NON_URGENT,
                "keywords": ["itching", "skin irritation", "rash", "scratching", "skin"],
                "steps": [
                    "Check the skin for redness, swelling, discharge, or parasites.",
                    "Keep the enclosure clean and remove possible irritants.",
                    "Prevent excessive scratching where possible.",
                    "Schedule a vet check if irritation spreads or does not improve.",
                ],
                "warningNotes": "Do not apply human creams, sprays, or powders unless advised by a veterinarian.",
            },
        }

        for species, speciesLabel in smallPetSpeciesLabels.items():
            for template in smallPetGuideTemplates.values():
                guides.append({
                    "title":        f"{template['title']} in {speciesLabel}",
                    "species":      species,
                    "urgencyLevel": template["urgencyLevel"],
                    "keywords":     template["keywords"],
                    "steps":        template["steps"],
                    "warningNotes": template["warningNotes"],
                    "approvedBy":   staff_id,
                    "isApproved":   True,
                })

        for guide in guides:
            if guide["title"] in obsoleteGuideTitles:
                continue
            if not self._firstAid.find_one({"title": guide["title"]}):
                self.insertFirstAidGuide(guide)
                logger.info("Seeded first aid guide: %s", guide["title"])

        # ------------------------------------------------------------------
        # 5. INSTRUCTIONAL VIDEOS
        # ------------------------------------------------------------------
        self._videos.delete_many({
            "$or": [
                {"url": {"$regex": "example.com", "$options": "i"}},
                {"title": {"$in": [
                    "How to Perform Dog CPR",
                    "Recognising Heatstroke Symptoms",
                    "Cat Wound First Aid",
                ]}},
            ]
        })

        videos = [
            {
                "title":           "Dog First-Aid Video Guide",
                "species":         "dog",
                "url":             "https://youtu.be/p_Xw_LaofEQ?si=JDcjKQ1qJ1UbRIhD",
                "durationSeconds": 312,
                "description":     "Video guide for dog first-aid awareness and emergency response.",
                "uploadedBy":      vet1_id,
                "isApproved":      True,
                "viewCount":       0,
                "tags":            ["dog", "first aid", "emergency"],
            },
            {
                "title":           "Cat First-Aid Video Guide",
                "species":         "cat",
                "url":             "https://youtu.be/vAqAxdhPFA8?si=kDoiVP9oUWA47-rr",
                "durationSeconds": 180,
                "description":     "Video guide for cat first-aid awareness and emergency response.",
                "uploadedBy":      vet1_id,
                "isApproved":      True,
                "viewCount":       0,
                "tags":            ["cat", "first aid", "emergency"],
            },
            {
                "title":           "Hamster First-Aid Video Guide",
                "species":         "hamster",
                "url":             "https://youtu.be/WcMnNj7uwxI?si=3QGzr_xrVLfQU_M1",
                "durationSeconds": 240,
                "description":     "Video guide for hamster care and first-aid awareness.",
                "uploadedBy":      vet1_id,
                "isApproved":      True,
                "viewCount":       0,
                "tags":            ["hamster", "first aid", "small pets"],
            },
            {
                "title":           "Guinea Pig First-Aid Video Guide",
                "species":         "guinea pig",
                "url":             "https://youtu.be/0tCVun6A9WI?si=9ian5EkMcIhVLfx1",
                "durationSeconds": 240,
                "description":     "Video guide for guinea pig care and first-aid awareness.",
                "uploadedBy":      vet1_id,
                "isApproved":      True,
                "viewCount":       0,
                "tags":            ["guinea pig", "first aid", "small pets"],
            },
            {
                "title":           "Bird First-Aid Video Guide",
                "species":         "bird",
                "url":             "https://youtu.be/ZxI7m-YiPZE?si=0-sJDStul8YxN2Fp",
                "durationSeconds": 240,
                "description":     "Video guide for bird care and first-aid awareness.",
                "uploadedBy":      vet1_id,
                "isApproved":      True,
                "viewCount":       0,
                "tags":            ["bird", "first aid", "small pets"],
            },
        ]

        for video in videos:
            if not self._videos.find_one({"title": video["title"]}):
                self.insertVideo(video)
                logger.info("Seeded video: %s", video["title"])

        # ------------------------------------------------------------------
        # 6. REGIONAL ALERTS
        # ------------------------------------------------------------------
        self._alerts.delete_many({
            "$or": [
                {"title": {"$regex": "Klang Valley|Kuala Lumpur|KL", "$options": "i"}},
                {"description": {"$regex": "Klang Valley|Kuala Lumpur|KL", "$options": "i"}},
                {"region": {"$regex": "Klang Valley|Kuala Lumpur|KL", "$options": "i"}},
            ]
        })

        alerts = [
            {
                "title":       "Kuching Pet Vaccination Reminder",
                "description": "Demo advisory: Pet owners in Kuching should keep dog and cat vaccination records up to date and contact local veterinary clinics for appointment availability.",
                "region":      "Kuching",
                "severity":    URGENCY_NON_URGENT,
                "isActive":    True,
                "createdBy":   staff_id,
            },
            {
                "title":       "Miri Heat Stress Advisory",
                "description": "Demo advisory: During hot weather in Miri, keep pets shaded, hydrated, and avoid outdoor activity during peak afternoon heat.",
                "region":      "Miri",
                "severity":    URGENCY_URGENT,
                "isActive":    True,
                "createdBy":   staff_id,
            },
            {
                "title":       "Bintulu Tick and Flea Prevention Advisory",
                "description": "Demo advisory: Pet owners in Bintulu should check pets for ticks and fleas after outdoor activity and seek veterinary advice for safe preventatives.",
                "region":      "Bintulu",
                "severity":    URGENCY_NON_URGENT,
                "isActive":    True,
                "createdBy":   staff_id,
            },
            {
                "title":       "Sibu Puppy and Kitten Illness Watch",
                "description": "Demo advisory: Young pets in Sibu showing vomiting, diarrhoea, weakness, or loss of appetite should be checked by a veterinarian promptly.",
                "region":      "Sibu",
                "severity":    URGENCY_URGENT,
                "isActive":    True,
                "createdBy":   staff_id,
            },
        ]

        for alert in alerts:
            if not self._alerts.find_one({"title": alert["title"]}):
                self.insertAlert(alert)
                logger.info("Seeded regional alert: %s", alert["title"])

        # ------------------------------------------------------------------
        # 7. EDUCATIONAL QUIZ
        # ------------------------------------------------------------------
        if not self._quizzes.find_one({"title": "Dog First Aid Basics"}):
            self.insertQuiz({
                "title":           "Dog First Aid Basics",
                "topic":           "first aid",
                "difficultyLevel": "beginner",
                "createdBy":       staff_id,
                "questions": [
                    {
                        "questionId":   "Q001",
                        "questionText": "What is the first action when a dog is choking?",
                        "options": [
                            "A. Perform blind finger sweep",
                            "B. Stay calm and look for visible foreign objects",
                            "C. Give the dog water",
                            "D. Leave the dog to cough it out",
                        ],
                        "correctAnswer": "B",
                        "feedback":  {
                            "explanationText": "Blind sweeps can push the object deeper. "
                                               "Only remove if the object is clearly visible."
                        },
                    },
                    {
                        "questionId":   "Q002",
                        "questionText": "Which should you NOT use to cool a dog with heatstroke?",
                        "options": [
                            "A. Cool water",
                            "B. Fanning",
                            "C. Ice-cold water or ice packs",
                            "D. Shaded area",
                        ],
                        "correctAnswer": "C",
                        "feedback":  {
                            "explanationText": "Ice-cold water causes rapid vasoconstriction "
                                               "and may lead to shock."
                        },
                    },
                    {
                        "questionId":   "Q003",
                        "questionText": "How long should a seizure last before calling an "
                                        "emergency vet?",
                        "options": [
                            "A. 1 minute",
                            "B. 3 minutes",
                            "C. 5 minutes",
                            "D. 10 minutes",
                        ],
                        "correctAnswer": "C",
                        "feedback":  {
                            "explanationText": "A seizure lasting over 5 minutes (status epilepticus) "
                                               "is a veterinary emergency."
                        },
                    },
                ],
            })
            logger.info("Seeded educational quiz.")

        if not self._quizzes.find_one({"title": "Cat Emergency Basics"}):
            self.insertQuiz({
                "title":           "Cat Emergency Basics",
                "topic":           "cat first aid",
                "difficultyLevel": "beginner",
                "createdBy":       staff_id,
                "questions": [
                    {
                        "questionId":   "C001",
                        "questionText": "What should you do if a cat is breathing with its mouth open?",
                        "options": [
                            "A. Wait and observe for a full day",
                            "B. Give human cough medicine",
                            "C. Keep the cat calm and seek emergency veterinary care",
                            "D. Force the cat to drink water",
                        ],
                        "correctAnswer": "C",
                        "feedback": {
                            "explanationText": "Open-mouth breathing in cats is an emergency and needs urgent veterinary care."
                        },
                    },
                    {
                        "questionId":   "C002",
                        "questionText": "Which product should never be used on cats?",
                        "options": [
                            "A. Clean water",
                            "B. Dog flea treatment",
                            "C. A clean towel",
                            "D. A quiet carrier",
                        ],
                        "correctAnswer": "B",
                        "feedback": {
                            "explanationText": "Some dog flea products are toxic to cats and can cause serious poisoning."
                        },
                    },
                    {
                        "questionId":   "C003",
                        "questionText": "Why should a limping cat be monitored closely?",
                        "options": [
                            "A. Cats often hide pain",
                            "B. Limping always means the cat is playing",
                            "C. Cats cannot injure their legs",
                            "D. It is never a veterinary issue",
                        ],
                        "correctAnswer": "A",
                        "feedback": {
                            "explanationText": "Cats may hide pain, so persistent limping should be checked by a vet."
                        },
                    },
                ],
            })
            logger.info("Seeded cat educational quiz.")

        if not self._quizzes.find_one({"title": "Pet Safety and Prevention"}):
            self.insertQuiz({
                "title":           "Pet Safety and Prevention",
                "topic":           "prevention",
                "species":         "dog",
                "difficultyLevel": "beginner",
                "createdBy":       staff_id,
                "questions": [
                    {
                        "questionId":   "P001",
                        "questionText": "Why should pet owners keep emergency clinic information available?",
                        "options": [
                            "A. It helps owners act quickly during emergencies",
                            "B. It replaces veterinary treatment",
                            "C. It is only useful for staff users",
                            "D. It prevents all pet illnesses",
                        ],
                        "correctAnswer": "A",
                        "feedback": {
                            "explanationText": "Quick access to clinic information helps owners respond faster in emergencies."
                        },
                    },
                    {
                        "questionId":   "P002",
                        "questionText": "What is a good reason to keep pet profiles updated?",
                        "options": [
                            "A. To make the app look full",
                            "B. To reuse accurate pet details during triage",
                            "C. To avoid all future vet visits",
                            "D. To remove the need for first-aid guidance",
                        ],
                        "correctAnswer": "B",
                        "feedback": {
                            "explanationText": "Updated pet profiles help triage use accurate species, age, and medical details."
                        },
                    },
                    {
                        "questionId":   "P003",
                        "questionText": "What should owners do before giving pets human medication?",
                        "options": [
                            "A. Give a smaller dose",
                            "B. Mix it with food",
                            "C. Ask a veterinarian first",
                            "D. Use any medicine labelled for children",
                        ],
                        "correctAnswer": "C",
                        "feedback": {
                            "explanationText": "Human medication can be dangerous for pets and should only be given with veterinary advice."
                        },
                    },
                ],
            })
            logger.info("Seeded prevention educational quiz.")

        quizSpeciesLabels = {
            "dog": "Dog",
            "cat": "Cat",
            "rabbit": "Rabbit",
            "hamster": "Hamster",
            "guinea pig": "Guinea Pig",
            "bird": "Bird",
            "tortoise": "Tortoise",
        }
        quizTopicTemplates = {
            "breathing": {
                "label": "Breathing Difficulty",
                "questions": [
                    {
                        "text": "What should you do first if your {pet} has breathing difficulty?",
                        "options": [
                            "A. Keep the pet calm and limit handling",
                            "B. Force the pet to drink water",
                            "C. Give human cough medicine",
                            "D. Wait until tomorrow",
                        ],
                        "answer": "A",
                        "feedback": "Breathing problems can worsen quickly. Keeping the pet calm and seeking veterinary help is safest.",
                    },
                    {
                        "text": "Which sign makes breathing difficulty more serious?",
                        "options": [
                            "A. Normal eating",
                            "B. Quiet resting",
                            "C. Open-mouth breathing or severe weakness",
                            "D. Sleeping after play",
                        ],
                        "answer": "C",
                        "feedback": "Open-mouth breathing or weakness can indicate an emergency and should not be ignored.",
                    },
                ],
            },
            "bleeding": {
                "label": "Bleeding / Wound Care",
                "questions": [
                    {
                        "text": "What is a safe first step for minor bleeding in a {pet}?",
                        "options": [
                            "A. Apply gentle pressure with clean gauze",
                            "B. Rub the wound strongly",
                            "C. Apply human antiseptic immediately",
                            "D. Ignore it if the pet is moving",
                        ],
                        "answer": "A",
                        "feedback": "Gentle pressure helps slow bleeding while reducing further injury.",
                    },
                    {
                        "text": "When should a wound be checked by a veterinarian?",
                        "options": [
                            "A. Only after one month",
                            "B. If bleeding continues or the wound is deep",
                            "C. Never, wounds heal alone",
                            "D. Only if the pet refuses treats",
                        ],
                        "answer": "B",
                        "feedback": "Deep or continuing bleeding can become serious, especially for small pets.",
                    },
                ],
            },
            "digestive": {
                "label": "Vomiting / Digestive Issues",
                "questions": [
                    {
                        "text": "What should you do if your {pet} shows repeated digestive distress?",
                        "options": [
                            "A. Monitor closely and contact a veterinarian",
                            "B. Give spicy food",
                            "C. Force-feed a large meal",
                            "D. Give human stomach medicine",
                        ],
                        "answer": "A",
                        "feedback": "Repeated digestive symptoms can lead to dehydration or indicate a serious condition.",
                    },
                    {
                        "text": "Which is a warning sign during digestive illness?",
                        "options": [
                            "A. Normal behaviour",
                            "B. Bright alertness",
                            "C. Weakness, bloating, blood, or not eating",
                            "D. Drinking normally",
                        ],
                        "answer": "C",
                        "feedback": "Weakness, bloating, blood, or appetite loss may need prompt veterinary care.",
                    },
                ],
            },
            "injury": {
                "label": "Limping / Injury",
                "questions": [
                    {
                        "text": "What should you do if your {pet} starts limping?",
                        "options": [
                            "A. Limit movement and check gently for injury",
                            "B. Force the pet to exercise",
                            "C. Pull the injured limb",
                            "D. Give human painkillers",
                        ],
                        "answer": "A",
                        "feedback": "Limiting movement prevents further injury while you assess the situation.",
                    },
                    {
                        "text": "Why should you avoid human painkillers?",
                        "options": [
                            "A. They are always tasty",
                            "B. They may be toxic to pets",
                            "C. They work for every species",
                            "D. They remove the need for a vet",
                        ],
                        "answer": "B",
                        "feedback": "Many human medicines are dangerous for pets and should only be used with veterinary advice.",
                    },
                ],
            },
            "skin": {
                "label": "Skin Irritation",
                "questions": [
                    {
                        "text": "What should you check for when your {pet} is scratching often?",
                        "options": [
                            "A. Redness, swelling, wounds, or parasites",
                            "B. Shoe size",
                            "C. Favourite toy colour",
                            "D. Internet popularity",
                        ],
                        "answer": "A",
                        "feedback": "Visible skin changes or parasites can help identify the cause of irritation.",
                    },
                    {
                        "text": "What should you avoid applying without veterinary advice?",
                        "options": [
                            "A. Clean water if appropriate",
                            "B. Human creams, sprays, or powders",
                            "C. A clean towel",
                            "D. A clean enclosure",
                        ],
                        "answer": "B",
                        "feedback": "Human skin products can irritate or poison pets depending on the species.",
                    },
                ],
            },
        }

        for species, speciesLabel in quizSpeciesLabels.items():
            for topic, template in quizTopicTemplates.items():
                title = f"{speciesLabel} {template['label']} Quiz"
                if self._quizzes.find_one({"title": title}):
                    continue

                questions = []
                for index, question in enumerate(template["questions"], start=1):
                    questions.append({
                        "questionId": f"{species.replace(' ', '_')}_{topic}_{index}",
                        "questionText": question["text"].format(pet=speciesLabel.lower()),
                        "options": question["options"],
                        "correctAnswer": question["answer"],
                        "feedback": {
                            "explanationText": question["feedback"],
                        },
                    })

                self.insertQuiz({
                    "title":           title,
                    "topic":           topic,
                    "species":         species,
                    "difficultyLevel": "beginner",
                    "createdBy":       staff_id,
                    "questions":       questions,
                })
                logger.info("Seeded quiz: %s", title)

        logger.info("seed_data() complete.")

    # ==================================================================
    # UTILITY
    # ==================================================================

    def closeConnection(self):
        """
        Close the underlying MongoDB client connection gracefully.

        Should be called during application teardown (e.g. Flask
        ``atexit`` handler) to flush any pending writes and release
        socket resources.
        """
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed.")
