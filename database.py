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
        Insert a veterinary partner details document.

        Parameters
        ----------
        vetDocument : dict
            Includes ``userId``, ``clinicName``, ``licenseNumber``,
            ``specialisations``, ``region``, and ``contactInfo``.

        Returns
        -------
        str
            The ``_id`` of the inserted record.
        """
        vetDocument["createdAt"] = datetime.now(timezone.utc)
        result = self._vetDetails.insert_one(vetDocument)
        return str(result.inserted_id)

    def findVetByUserId(self, userId: str) -> dict | None:
        """
        Retrieve vet details linked to a specific user account.

        Parameters
        ----------
        userId : str

        Returns
        -------
        dict or None
        """
        return self._vetDetails.find_one({"userId": userId})

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
        return list(self._vetDetails.find({"region": region, "isActive": True}))

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
        return list(self._alerts.find({"region": region, "isActive": True}))

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

    def recordQuizFeedback(self, quizId: str, feedbackDocument: dict) -> dict | None:
        """
        Atomically append a feedback entry to a quiz's ``feedbackList`` array.

        Uses ``$push`` to guarantee the append is atomic and no concurrent
        write can corrupt the array.

        Parameters
        ----------
        quizId : str
        feedbackDocument : dict
            The feedback payload (score, comments, submittedBy, etc.).

        Returns
        -------
        dict or None
            The updated quiz document.
        """
        feedbackDocument["submittedAt"] = datetime.now(timezone.utc)
        return self._quizzes.find_one_and_update(
            {"_id": ObjectId(quizId)},
            {"$push": {"feedbackList": feedbackDocument}},
            return_document=pymongo.ReturnDocument.AFTER
        )

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
                "region":       "Kuala Lumpur",
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
        if not self._vetDetails.find_one({"userId": vet1_id}):
            self.insertVetDetails({
                "userId":      vet1_id,
                "clinicName":  "PetCare Veterinary Clinic",
                "licenseNumber": "VET-MY-00123",
                "specialisations": ["small animals", "emergency care"],
                "region":      "Kuala Lumpur",
                "contactInfo": {
                    "phone":   "+60312345678",
                    "address": "123 Jalan Ampang, KL",
                    "email":   "dr.tan@vetclinic.com"
                },
                "isActive":    True,
            })
            logger.info("Seeded vet details for dr.tan.")

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
        guides = [
            {
                "title":        "Choking in Dogs",
                "species":      "dog",
                "urgencyLevel": URGENCY_EMERGENCY,
                "keywords":     ["choking", "airway obstruction", "coughing", "gagging"],
                "steps": [
                    "Stay calm and restrain the dog safely.",
                    "Open the mouth and look for visible foreign objects.",
                    "If visible, sweep with a finger — do NOT perform blind sweeps.",
                    "For small dogs: hold upside-down and give 5 firm back blows.",
                    "For large dogs: apply modified Heimlich — fist behind last rib, "
                    "thrust upward and inward 5 times.",
                    "If unconscious: begin pet CPR and rush to vet immediately.",
                ],
                "warningNotes": "Do not leave the animal alone. Seek emergency vet care "
                                "even after successful removal.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Heatstroke in Dogs",
                "species":      "dog",
                "urgencyLevel": URGENCY_EMERGENCY,
                "keywords":     ["heatstroke", "overheating", "panting", "collapse", "heat"],
                "steps": [
                    "Move the dog to a cool, shaded area immediately.",
                    "Apply cool (not ice-cold) water to paws, groin, armpits, and neck.",
                    "Fan the dog to aid evaporative cooling.",
                    "Offer small sips of cool water if conscious.",
                    "Monitor rectal temperature — target below 39.5 °C.",
                    "Transport to veterinary clinic urgently.",
                ],
                "warningNotes": "Never use ice or ice-cold water — rapid cooling can cause shock.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Minor Wound Care for Cats",
                "species":      "cat",
                "urgencyLevel": URGENCY_NON_URGENT,
                "keywords":     ["wound", "cut", "scratch", "bleeding", "laceration"],
                "steps": [
                    "Wear gloves — even friendly cats may bite when in pain.",
                    "Apply gentle pressure with a clean cloth to stop bleeding.",
                    "Clean with saline solution or clean running water.",
                    "Do not use hydrogen peroxide or alcohol — they damage tissue.",
                    "Apply pet-safe antiseptic if available.",
                    "Monitor for signs of infection over 48 hours.",
                    "Seek vet care if wound is deep, gaping, or does not stop bleeding.",
                ],
                "warningNotes": "Cat bites and scratches carry high infection risk — "
                                "consult vet if redness or swelling develops.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
            {
                "title":        "Seizures in Dogs",
                "species":      "dog",
                "urgencyLevel": URGENCY_URGENT,
                "keywords":     ["seizure", "convulsion", "fitting", "epilepsy", "tremors"],
                "steps": [
                    "Do NOT restrain the dog or put hands near the mouth.",
                    "Clear the surrounding area of hard or sharp objects.",
                    "Time the seizure — note start and end time.",
                    "Keep room dark and quiet to reduce stimulation.",
                    "After the seizure: keep dog warm and calm.",
                    "If seizure lasts > 5 minutes or multiple seizures in 24 hrs: "
                    "emergency vet immediately.",
                ],
                "warningNotes": "Dogs do not swallow their tongue during seizures — "
                                "do not attempt to open the mouth.",
                "approvedBy":   staff_id,
                "isApproved":   True,
            },
        ]

        for guide in guides:
            if not self._firstAid.find_one({"title": guide["title"]}):
                self.insertFirstAidGuide(guide)
                logger.info("Seeded first aid guide: %s", guide["title"])

        # ------------------------------------------------------------------
        # 5. INSTRUCTIONAL VIDEOS
        # ------------------------------------------------------------------
        videos = [
            {
                "title":           "How to Perform Dog CPR",
                "species":         "dog",
                "url":             "https://example.com/videos/dog-cpr",
                "durationSeconds": 312,
                "description":     "Step-by-step guide to performing CPR on a dog, "
                                   "including chest compressions and rescue breathing.",
                "uploadedBy":      vet1_id,
                "isApproved":      True,
                "viewCount":       0,
                "tags":            ["cpr", "resuscitation", "emergency"],
            },
            {
                "title":           "Recognising Heatstroke Symptoms",
                "species":         "dog",
                "url":             "https://example.com/videos/dog-heatstroke",
                "durationSeconds": 180,
                "description":     "Visual guide to identifying heatstroke symptoms in dogs.",
                "uploadedBy":      vet1_id,
                "isApproved":      True,
                "viewCount":       0,
                "tags":            ["heatstroke", "symptoms", "prevention"],
            },
            {
                "title":           "Cat Wound First Aid",
                "species":         "cat",
                "url":             "https://example.com/videos/cat-wound-care",
                "durationSeconds": 240,
                "description":     "Demonstration of safe wound cleaning and bandaging for cats.",
                "uploadedBy":      vet1_id,
                "isApproved":      True,
                "viewCount":       0,
                "tags":            ["wound", "first aid", "cat"],
            },
        ]

        for video in videos:
            if not self._videos.find_one({"title": video["title"]}):
                self.insertVideo(video)
                logger.info("Seeded video: %s", video["title"])

        # ------------------------------------------------------------------
        # 6. REGIONAL ALERTS
        # ------------------------------------------------------------------
        if not self._alerts.find_one({"title": "Canine Parvovirus Outbreak — Klang Valley"}):
            self.insertAlert({
                "title":       "Canine Parvovirus Outbreak — Klang Valley",
                "description": "Multiple unvaccinated dogs in Klang Valley have tested "
                               "positive for parvovirus. Ensure dogs are vaccinated and "
                               "avoid contact with unknown dogs.",
                "region":      "Kuala Lumpur",
                "severity":    URGENCY_URGENT,
                "isActive":    True,
                "createdBy":   staff_id,
            })
            logger.info("Seeded regional alert.")

        # ------------------------------------------------------------------
        # 7. EDUCATIONAL QUIZ
        # ------------------------------------------------------------------
        if not self._quizzes.find_one({"title": "Dog First Aid Basics"}):
            self.insertQuiz({
                "title":           "Dog First Aid Basics",
                "topic":           "first aid",
                "difficultyLevel": "beginner",
                "createdBy":       staff_id,
                "feedbackList":    [],
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
                        "explanation":  "Blind sweeps can push the object deeper. "
                                        "Only remove if the object is clearly visible.",
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
                        "explanation":  "Ice-cold water causes rapid vasoconstriction "
                                        "and may lead to shock.",
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
                        "explanation":  "A seizure lasting over 5 minutes (status epilepticus) "
                                        "is a veterinary emergency.",
                    },
                ],
            })
            logger.info("Seeded educational quiz.")

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