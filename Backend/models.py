"""
models.py — Domain / Entity Layer

Pet First-Aid Web Application

This module defines lightweight **entity classes** that act as data containers
for the application's domain objects.  Each class:

* Enforces immediate field-level constraints in ``__init__`` (type checks,
  required-field presence, value range validation).
* Provides a ``toDict()`` serialisation method for passing data to the
  ``Database`` layer and for constructing HTTP responses.
* Provides a ``fromDict()`` class-method factory for rehydrating objects
  from MongoDB documents.
* Contains **no** database calls — those belong exclusively to ``database.py``.
* Contains **no** business logic — that belongs exclusively to ``services.py``.

Architecture tier : Domain Layer (Tier 2 of 5)
Conventions       : PascalCase classes · camelCase methods/attributes ·
                    UPPER_SNAKE_CASE constants · triple-quoted docstrings
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
ROLE_PET_OWNER         = "pet_owner"
ROLE_ASSOCIATION_STAFF = "association_staff"
ROLE_VET_PARTNER       = "veterinary_partner"
VALID_ROLES            = {ROLE_PET_OWNER, ROLE_ASSOCIATION_STAFF, ROLE_VET_PARTNER}

SPECIES_DOG     = "dog"
SPECIES_CAT     = "cat"
SPECIES_RABBIT  = "rabbit"
SPECIES_HAMSTER = "hamster"
SPECIES_GUINEA_PIG = "guinea pig"
SPECIES_BIRD    = "bird"
SPECIES_TORTOISE = "tortoise"
VALID_SPECIES   = {
    SPECIES_DOG,
    SPECIES_CAT,
    SPECIES_RABBIT,
    SPECIES_HAMSTER,
    SPECIES_GUINEA_PIG,
    SPECIES_BIRD,
    SPECIES_TORTOISE,
}

URGENCY_EMERGENCY  = "EMERGENCY"
URGENCY_URGENT     = "URGENT"
URGENCY_NON_URGENT = "NON_URGENT"
VALID_URGENCY      = {URGENCY_EMERGENCY, URGENCY_URGENT, URGENCY_NON_URGENT}

STATUS_PENDING  = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
VALID_STATUSES  = {STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED}

DIFFICULTY_BEGINNER     = "beginner"
DIFFICULTY_INTERMEDIATE = "intermediate"
DIFFICULTY_ADVANCED     = "advanced"
VALID_DIFFICULTIES      = {DIFFICULTY_BEGINNER, DIFFICULTY_INTERMEDIATE, DIFFICULTY_ADVANCED}

EMAIL_REGEX = re.compile(r"^[\w.\-+]+@[\w\-]+\.[a-zA-Z]{2,}$")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _requireNonEmpty(value: Any, fieldName: str) -> None:
    """Raise ``ValueError`` if *value* is ``None`` or an empty string."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"'{fieldName}' is required and must not be empty.")


def _requireType(value: Any, expectedType: type, fieldName: str) -> None:
    """Raise ``TypeError`` if *value* is not an instance of *expectedType*."""
    if not isinstance(value, expectedType):
        raise TypeError(
            f"'{fieldName}' must be of type {expectedType.__name__}, "
            f"got {type(value).__name__}."
        )


# ===========================================================================
# ABSTRACT BASE CLASS — User
# ===========================================================================

class User(ABC):
    """
    Abstract base class for all user roles in the system.

    Enforces the common identity attributes shared by ``PetOwner``,
    ``AssociationStaff``, and ``VeterinaryPartner``.  Subclasses must
    implement ``getRole()`` and ``toDict()``.

    Attributes
    ----------
    userId : str
        MongoDB ``_id`` as a hex string (empty string for unsaved entities).
    email : str
        Validated email address (stored in lower-case).
    fullName : str
        Display name of the user.
    passwordHash : str
        Bcrypt/argon2 hash of the user's password (never store plaintext).
    isActive : bool
        Whether the account is enabled.
    createdAt : datetime
        UTC timestamp of account creation.
    """

    def __init__(
        self,
        email:        str,
        fullName:     str,
        passwordHash: str,
        userId:       str       = "",
        isActive:     bool      = True,
        createdAt:    datetime | None = None,
    ) -> None:
        """
        Initialise common User fields with immediate validation.

        Parameters
        ----------
        email : str
        fullName : str
        passwordHash : str
        userId : str, optional
        isActive : bool, optional
        createdAt : datetime, optional
        """
        _requireNonEmpty(email,        "email")
        _requireNonEmpty(fullName,     "fullName")
        _requireNonEmpty(passwordHash, "passwordHash")

        if not EMAIL_REGEX.match(email.strip().lower()):
            raise ValueError(f"'{email}' is not a valid email address.")

        self.userId       = userId
        self.email        = email.strip().lower()
        self.fullName     = fullName.strip()
        self.passwordHash = passwordHash
        self.isActive     = bool(isActive)
        self.createdAt    = createdAt or datetime.now(timezone.utc)

    @abstractmethod
    def getRole(self) -> str:
        """
        Return the role identifier string for this user type.

        Returns
        -------
        str
            One of the ``ROLE_*`` constants.
        """

    @abstractmethod
    def toDict(self) -> dict:
        """
        Serialise the entity to a plain ``dict`` suitable for MongoDB or JSON.

        Returns
        -------
        dict
        """

    def _baseDict(self) -> dict:
        """
        Return a dict of the common ``User`` fields.

        Used by subclass ``toDict()`` implementations to avoid repetition.

        Returns
        -------
        dict
        """
        return {
            "email":        self.email,
            "fullName":     self.fullName,
            "passwordHash": self.passwordHash,
            "role":         self.getRole(),
            "isActive":     self.isActive,
            "createdAt":    self.createdAt,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} email={self.email!r} id={self.userId!r}>"


# ===========================================================================
# CONCRETE USER SUBCLASSES
# ===========================================================================

class PetOwner(User):
    """
    Represents a registered pet owner who uses the application.

    Extends ``User`` with contact and region information relevant to
    displaying localised alerts and vet finder results.

    Attributes
    ----------
    phoneNumber : str
        Contact phone number (optional).
    region : str
        Geographic region (e.g. ``"Kuala Lumpur"``).
    """

    def __init__(
        self,
        email:        str,
        fullName:     str,
        passwordHash: str,
        phoneNumber:  str  = "",
        region:       str  = "",
        userId:       str  = "",
        isActive:     bool = True,
        createdAt:    datetime | None = None,
    ) -> None:
        """
        Initialise a ``PetOwner`` instance.

        Parameters
        ----------
        email : str
        fullName : str
        passwordHash : str
        phoneNumber : str, optional
        region : str, optional
        userId : str, optional
        isActive : bool, optional
        createdAt : datetime, optional
        """
        super().__init__(email, fullName, passwordHash, userId, isActive, createdAt)
        self.phoneNumber = phoneNumber.strip()
        self.region      = region.strip()

    def getRole(self) -> str:
        """Return the pet owner role constant."""
        return ROLE_PET_OWNER

    def toDict(self) -> dict:
        """
        Serialise ``PetOwner`` to a dict.

        Returns
        -------
        dict
        """
        data = self._baseDict()
        data.update({
            "phoneNumber": self.phoneNumber,
            "region":      self.region,
        })
        return data

    @classmethod
    def fromDict(cls, data: dict) -> "PetOwner":
        """
        Construct a ``PetOwner`` from a MongoDB document dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        PetOwner
        """
        return cls(
            email        = data.get("email",        ""),
            fullName     = data.get("fullName",     ""),
            passwordHash = data.get("passwordHash", ""),
            phoneNumber  = data.get("phoneNumber",  ""),
            region       = data.get("region",       ""),
            userId       = str(data.get("_id",      "")),
            isActive     = data.get("isActive",     True),
            createdAt    = data.get("createdAt"),
        )


class AssociationStaff(User):
    """
    Represents an internal staff member of the pet welfare association.

    Staff accounts have elevated permissions to moderate content,
    broadcast alerts, and manage user accounts.

    Attributes
    ----------
    staffId : str
        Internal employee ID.
    department : str
        Department the staff member belongs to.
    permissions : list[str]
        List of permission strings granted to this account.
    """

    def __init__(
        self,
        email:       str,
        fullName:    str,
        passwordHash:str,
        staffId:     str,
        department:  str       = "",
        permissions: list[str] = None,
        userId:      str       = "",
        isActive:    bool      = True,
        createdAt:   datetime | None = None,
    ) -> None:
        """
        Initialise an ``AssociationStaff`` instance.

        Parameters
        ----------
        email : str
        fullName : str
        passwordHash : str
        staffId : str
            Required internal staff identifier.
        department : str, optional
        permissions : list[str], optional
        userId : str, optional
        isActive : bool, optional
        createdAt : datetime, optional
        """
        super().__init__(email, fullName, passwordHash, userId, isActive, createdAt)
        _requireNonEmpty(staffId, "staffId")
        self.staffId     = staffId.strip()
        self.department  = department.strip()
        self.permissions = permissions if permissions is not None else []

    def getRole(self) -> str:
        """Return the association staff role constant."""
        return ROLE_ASSOCIATION_STAFF

    def hasPermission(self, permission: str) -> bool:
        """
        Check whether this staff member holds a specific permission.

        Parameters
        ----------
        permission : str

        Returns
        -------
        bool
        """
        return permission in self.permissions

    def toDict(self) -> dict:
        """
        Serialise ``AssociationStaff`` to a dict.

        Returns
        -------
        dict
        """
        data = self._baseDict()
        data.update({
            "staffId":     self.staffId,
            "department":  self.department,
            "permissions": self.permissions,
        })
        return data

    @classmethod
    def fromDict(cls, data: dict) -> "AssociationStaff":
        """
        Construct an ``AssociationStaff`` from a MongoDB document dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        AssociationStaff
        """
        return cls(
            email        = data.get("email",        ""),
            fullName     = data.get("fullName",     ""),
            passwordHash = data.get("passwordHash", ""),
            staffId      = data.get("staffId",      ""),
            department   = data.get("department",   ""),
            permissions  = data.get("permissions",  []),
            userId       = str(data.get("_id",      "")),
            isActive     = data.get("isActive",     True),
            createdAt    = data.get("createdAt"),
        )


class VeterinaryPartner(User):
    """
    Represents a verified veterinary professional partnered with the association.

    Vet partners can submit first aid content for moderation approval.

    Attributes
    ----------
    licenseNumber : str
        Official veterinary license number.
    specialisations : list[str]
        Areas of expertise (e.g. ``["small animals", "emergency care"]``).
    isVerified : bool
        ``True`` once the association has verified the license.
    """

    def __init__(
        self,
        email:           str,
        fullName:        str,
        passwordHash:    str,
        licenseNumber:   str,
        specialisations: list[str] = None,
        isVerified:      bool      = False,
        userId:          str       = "",
        isActive:        bool      = True,
        createdAt:       datetime | None = None,
    ) -> None:
        """
        Initialise a ``VeterinaryPartner`` instance.

        Parameters
        ----------
        email : str
        fullName : str
        passwordHash : str
        licenseNumber : str
            Required and must be non-empty.
        specialisations : list[str], optional
        isVerified : bool, optional
        userId : str, optional
        isActive : bool, optional
        createdAt : datetime, optional
        """
        super().__init__(email, fullName, passwordHash, userId, isActive, createdAt)
        _requireNonEmpty(licenseNumber, "licenseNumber")
        self.licenseNumber   = licenseNumber.strip()
        self.specialisations = specialisations if specialisations is not None else []
        self.isVerified      = bool(isVerified)

    def getRole(self) -> str:
        """Return the veterinary partner role constant."""
        return ROLE_VET_PARTNER

    def toDict(self) -> dict:
        """
        Serialise ``VeterinaryPartner`` to a dict.

        Returns
        -------
        dict
        """
        data = self._baseDict()
        data.update({
            "licenseNumber":   self.licenseNumber,
            "specialisations": self.specialisations,
            "isVerified":      self.isVerified,
        })
        return data

    @classmethod
    def fromDict(cls, data: dict) -> "VeterinaryPartner":
        """
        Construct a ``VeterinaryPartner`` from a MongoDB document dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        VeterinaryPartner
        """
        return cls(
            email           = data.get("email",           ""),
            fullName        = data.get("fullName",        ""),
            passwordHash    = data.get("passwordHash",    ""),
            licenseNumber   = data.get("licenseNumber",   ""),
            specialisations = data.get("specialisations", []),
            isVerified      = data.get("isVerified",      False),
            userId          = str(data.get("_id",         "")),
            isActive        = data.get("isActive",        True),
            createdAt       = data.get("createdAt"),
        )


# ===========================================================================
# PET PROFILE
# ===========================================================================

class PetProfile:
    """
    Represents a single pet's profile belonging to a ``PetOwner``.

    Attributes
    ----------
    petId : str
        MongoDB ``_id`` as hex string.
    ownerId : str
        ``_id`` of the owning ``PetOwner``.
    name : str
        The pet's name.
    species : str
        One of the ``SPECIES_*`` constants.
    breed : str
        Breed or type description.
    age : int
        Age in whole years.
    weightKg : float
        Body weight in kilograms.
    sex : str
        ``"male"`` or ``"female"``.
    isNeutered : bool
        Whether the animal has been neutered/spayed.
    medicalHistory : list[str]
        Free-text medical history notes.
    emergencyNotes : str
        Critical information for emergency responders.
    """

    def __init__(
        self,
        ownerId:        str,
        name:           str,
        species:        str,
        breed:          str        = "",
        age:            int        = 0,
        weightKg:       float      = 0.0,
        sex:            str        = "",
        isNeutered:     bool       = False,
        medicalHistory: list[str]  = None,
        emergencyNotes: str        = "",
        petId:          str        = "",
        createdAt:      datetime | None = None,
    ) -> None:
        """
        Initialise a ``PetProfile`` with field validation.

        Parameters
        ----------
        ownerId : str
        name : str
        species : str
            Must be one of ``VALID_SPECIES``.
        breed : str, optional
        age : int, optional
        weightKg : float, optional
        sex : str, optional
        isNeutered : bool, optional
        medicalHistory : list[str], optional
        emergencyNotes : str, optional
        petId : str, optional
        createdAt : datetime, optional
        """
        _requireNonEmpty(ownerId, "ownerId")
        _requireNonEmpty(name,    "name")
        _requireNonEmpty(species, "species")

        if species.lower() not in VALID_SPECIES:
            raise ValueError(
                f"Invalid species '{species}'. Must be one of {VALID_SPECIES}."
            )
        if age < 0:
            raise ValueError("'age' cannot be negative.")
        if weightKg < 0:
            raise ValueError("'weightKg' cannot be negative.")

        self.petId          = petId
        self.ownerId        = ownerId
        self.name           = name.strip()
        self.species        = species.lower()
        self.breed          = breed.strip()
        self.age            = int(age)
        self.weightKg       = float(weightKg)
        self.sex            = sex.lower().strip()
        self.isNeutered     = bool(isNeutered)
        self.medicalHistory = medicalHistory if medicalHistory is not None else []
        self.emergencyNotes = emergencyNotes.strip()
        self.createdAt      = createdAt or datetime.now(timezone.utc)

    def toDict(self) -> dict:
        """
        Serialise ``PetProfile`` to a dict.

        Returns
        -------
        dict
        """
        return {
            "ownerId":        self.ownerId,
            "name":           self.name,
            "species":        self.species,
            "breed":          self.breed,
            "age":            self.age,
            "weightKg":       self.weightKg,
            "sex":            self.sex,
            "isNeutered":     self.isNeutered,
            "medicalHistory": self.medicalHistory,
            "emergencyNotes": self.emergencyNotes,
            "createdAt":      self.createdAt,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "PetProfile":
        """
        Construct a ``PetProfile`` from a MongoDB document dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        PetProfile
        """
        return cls(
            ownerId        = data.get("ownerId",        ""),
            name           = data.get("name",           ""),
            species        = data.get("species",        SPECIES_DOG),
            breed          = data.get("breed",          ""),
            age            = data.get("age",            0),
            weightKg       = data.get("weightKg",       0.0),
            sex            = data.get("sex",            ""),
            isNeutered     = data.get("isNeutered",     False),
            medicalHistory = data.get("medicalHistory", []),
            emergencyNotes = data.get("emergencyNotes", ""),
            petId          = str(data.get("_id",        "")),
            createdAt      = data.get("createdAt"),
        )

    def __repr__(self) -> str:
        return f"<PetProfile name={self.name!r} species={self.species!r} id={self.petId!r}>"


# ===========================================================================
# SYMPTOM
# ===========================================================================

class Symptom:
    """
    Represents a single symptom reported during a triage assessment.

    Attributes
    ----------
    symptomId : str
        Unique identifier (MongoDB ``_id`` or generated string).
    name : str
        Short symptom name (e.g. ``"vomiting"``).
    description : str
        Detailed description of the symptom presentation.
    associatedUrgency : str
        Baseline urgency level associated with this symptom.
    affectedSpecies : list[str]
        Species for which this symptom is relevant.
    """

    def __init__(
        self,
        name:              str,
        description:       str        = "",
        associatedUrgency: str        = URGENCY_NON_URGENT,
        affectedSpecies:   list[str]  = None,
        symptomId:         str        = "",
    ) -> None:
        """
        Initialise a ``Symptom`` instance.

        Parameters
        ----------
        name : str
        description : str, optional
        associatedUrgency : str, optional
        affectedSpecies : list[str], optional
        symptomId : str, optional
        """
        _requireNonEmpty(name, "name")
        if associatedUrgency not in VALID_URGENCY:
            raise ValueError(
                f"Invalid urgencyLevel '{associatedUrgency}'. "
                f"Must be one of {VALID_URGENCY}."
            )
        self.symptomId         = symptomId
        self.name              = name.strip().lower()
        self.description       = description.strip()
        self.associatedUrgency = associatedUrgency
        self.affectedSpecies   = affectedSpecies if affectedSpecies is not None else []

    def toDict(self) -> dict:
        """
        Serialise ``Symptom`` to a dict.

        Returns
        -------
        dict
        """
        return {
            "name":              self.name,
            "description":       self.description,
            "associatedUrgency": self.associatedUrgency,
            "affectedSpecies":   self.affectedSpecies,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "Symptom":
        """
        Construct a ``Symptom`` from a dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        Symptom
        """
        return cls(
            name              = data.get("name",              ""),
            description       = data.get("description",       ""),
            associatedUrgency = data.get("associatedUrgency", URGENCY_NON_URGENT),
            affectedSpecies   = data.get("affectedSpecies",   []),
            symptomId         = str(data.get("_id",           "")),
        )

    def __repr__(self) -> str:
        return f"<Symptom name={self.name!r} urgency={self.associatedUrgency!r}>"


# ===========================================================================
# FIRST AID GUIDE
# ===========================================================================

class FirstAidGuide:
    """
    Represents a structured first aid guide for a specific condition.

    Attributes
    ----------
    guideId : str
        MongoDB ``_id`` hex string.
    title : str
        Descriptive title of the guide.
    species : str
        Target species (one of ``VALID_SPECIES``).
    urgencyLevel : str
        Overall urgency rating for this condition.
    keywords : list[str]
        Symptom/condition keywords for search matching.
    steps : list[str]
        Ordered first aid action steps.
    warningNotes : str
        Critical warnings to display prominently.
    approvedBy : str
        ``_id`` of the staff member who approved the guide.
    isApproved : bool
        Publication status.
    """

    def __init__(
        self,
        title:        str,
        species:      str,
        urgencyLevel: str,
        steps:        list[str],
        keywords:     list[str]  = None,
        warningNotes: str        = "",
        approvedBy:   str        = "",
        isApproved:   bool       = False,
        guideId:      str        = "",
        createdAt:    datetime | None = None,
    ) -> None:
        """
        Initialise a ``FirstAidGuide`` with validation.

        Parameters
        ----------
        title : str
        species : str
        urgencyLevel : str
        steps : list[str]
            Must contain at least one step.
        keywords : list[str], optional
        warningNotes : str, optional
        approvedBy : str, optional
        isApproved : bool, optional
        guideId : str, optional
        createdAt : datetime, optional
        """
        _requireNonEmpty(title,   "title")
        _requireNonEmpty(species, "species")

        if species.lower() not in VALID_SPECIES:
            raise ValueError(f"Invalid species '{species}'.")
        if urgencyLevel not in VALID_URGENCY:
            raise ValueError(f"Invalid urgencyLevel '{urgencyLevel}'.")
        if not steps:
            raise ValueError("'steps' must contain at least one action.")

        self.guideId      = guideId
        self.title        = title.strip()
        self.species      = species.lower()
        self.urgencyLevel = urgencyLevel
        self.keywords     = keywords if keywords is not None else []
        self.steps        = steps
        self.warningNotes = warningNotes.strip()
        self.approvedBy   = approvedBy
        self.isApproved   = bool(isApproved)
        self.createdAt    = createdAt or datetime.now(timezone.utc)

    def toDict(self) -> dict:
        """
        Serialise ``FirstAidGuide`` to a dict.

        Returns
        -------
        dict
        """
        return {
            "title":        self.title,
            "species":      self.species,
            "urgencyLevel": self.urgencyLevel,
            "keywords":     self.keywords,
            "steps":        self.steps,
            "warningNotes": self.warningNotes,
            "approvedBy":   self.approvedBy,
            "isApproved":   self.isApproved,
            "createdAt":    self.createdAt,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "FirstAidGuide":
        """
        Construct a ``FirstAidGuide`` from a MongoDB document dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        FirstAidGuide
        """
        return cls(
            title        = data.get("title",        ""),
            species      = data.get("species",      SPECIES_DOG),
            urgencyLevel = data.get("urgencyLevel", URGENCY_NON_URGENT),
            steps        = data.get("steps",        [""]),
            keywords     = data.get("keywords",     []),
            warningNotes = data.get("warningNotes", ""),
            approvedBy   = data.get("approvedBy",   ""),
            isApproved   = data.get("isApproved",   False),
            guideId      = str(data.get("_id",      "")),
            createdAt    = data.get("createdAt"),
        )

    def __repr__(self) -> str:
        return f"<FirstAidGuide title={self.title!r} species={self.species!r}>"


# ===========================================================================
# INSTRUCTIONAL VIDEO
# ===========================================================================

class InstructionalVideo:
    """
    Represents an instructional video resource linked to a first aid topic.

    Attributes
    ----------
    videoId : str
        MongoDB ``_id`` hex string.
    title : str
    species : str
    url : str
        Publicly accessible video URL.
    durationSeconds : int
        Video length in seconds.
    description : str
    uploadedBy : str
        ``_id`` of the uploading ``VeterinaryPartner``.
    isApproved : bool
    viewCount : int
        Monotonically incremented view counter (updated atomically in DAL).
    tags : list[str]
    """

    def __init__(
        self,
        title:           str,
        species:         str,
        url:             str,
        durationSeconds: int        = 0,
        description:     str        = "",
        uploadedBy:      str        = "",
        isApproved:      bool       = False,
        viewCount:       int        = 0,
        tags:            list[str]  = None,
        videoId:         str        = "",
        uploadedAt:      datetime | None = None,
    ) -> None:
        """
        Initialise an ``InstructionalVideo``.

        Parameters
        ----------
        title : str
        species : str
        url : str
        durationSeconds : int, optional
        description : str, optional
        uploadedBy : str, optional
        isApproved : bool, optional
        viewCount : int, optional
        tags : list[str], optional
        videoId : str, optional
        uploadedAt : datetime, optional
        """
        _requireNonEmpty(title,   "title")
        _requireNonEmpty(species, "species")
        _requireNonEmpty(url,     "url")

        if species.lower() not in VALID_SPECIES:
            raise ValueError(f"Invalid species '{species}'.")
        if durationSeconds < 0:
            raise ValueError("'durationSeconds' cannot be negative.")

        self.videoId         = videoId
        self.title           = title.strip()
        self.species         = species.lower()
        self.url             = url.strip()
        self.durationSeconds = int(durationSeconds)
        self.description     = description.strip()
        self.uploadedBy      = uploadedBy
        self.isApproved      = bool(isApproved)
        self.viewCount       = max(0, int(viewCount))
        self.tags            = tags if tags is not None else []
        self.uploadedAt      = uploadedAt or datetime.now(timezone.utc)

    def toDict(self) -> dict:
        """
        Serialise ``InstructionalVideo`` to a dict.

        Returns
        -------
        dict
        """
        return {
            "title":           self.title,
            "species":         self.species,
            "url":             self.url,
            "durationSeconds": self.durationSeconds,
            "description":     self.description,
            "uploadedBy":      self.uploadedBy,
            "isApproved":      self.isApproved,
            "viewCount":       self.viewCount,
            "tags":            self.tags,
            "uploadedAt":      self.uploadedAt,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "InstructionalVideo":
        """
        Construct an ``InstructionalVideo`` from a MongoDB document dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        InstructionalVideo
        """
        return cls(
            title           = data.get("title",           ""),
            species         = data.get("species",         SPECIES_DOG),
            url             = data.get("url",             ""),
            durationSeconds = data.get("durationSeconds", 0),
            description     = data.get("description",     ""),
            uploadedBy      = data.get("uploadedBy",      ""),
            isApproved      = data.get("isApproved",      False),
            viewCount       = data.get("viewCount",       0),
            tags            = data.get("tags",            []),
            videoId         = str(data.get("_id",         "")),
            uploadedAt      = data.get("uploadedAt"),
        )

    def __repr__(self) -> str:
        return f"<InstructionalVideo title={self.title!r} species={self.species!r}>"


# ===========================================================================
# VET DETAILS
# ===========================================================================

class VetDetails:
    """
    Represents a veterinary clinic directory record.

    VetDetails is maintained by AssociationStaff and retrieved by region
    when pet owners search for nearby professional help.
    """

    def __init__(
        self,
        clinicName: str,
        licenseNumber: str,
        specialisations: list[str] = None,
        region: str = "",
        contactInfo: dict = None,
        operatingHours: str = "",
        isActive: bool = True,
        createdByStaffId: str = "",
        detailsId: str = "",
        createdAt: datetime | None = None,
    ) -> None:
        _requireNonEmpty(clinicName, "clinicName")
        _requireNonEmpty(licenseNumber, "licenseNumber")

        self.detailsId = detailsId
        self.clinicName = clinicName.strip()
        self.licenseNumber = licenseNumber.strip()
        self.specialisations = specialisations if specialisations is not None else []
        self.region = region.strip()
        self.contactInfo = contactInfo if contactInfo is not None else {}
        self.operatingHours = operatingHours.strip()
        self.isActive = bool(isActive)
        self.createdByStaffId = createdByStaffId
        self.createdAt = createdAt or datetime.now(timezone.utc)
        
    def toDict(self) -> dict:
        return {
            "clinicName": self.clinicName,
            "licenseNumber": self.licenseNumber,
            "specialisations": self.specialisations,
            "region": self.region,
            "contactInfo": self.contactInfo,
            "operatingHours": self.operatingHours,
            "isActive": self.isActive,
            "createdByStaffId": self.createdByStaffId,
            "createdAt": self.createdAt,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "VetDetails":
        return cls(
            clinicName=data.get("clinicName", ""),
            licenseNumber=data.get("licenseNumber", ""),
            specialisations=data.get("specialisations", []),
            region=data.get("region", ""),
            contactInfo=data.get("contactInfo", {}),
            operatingHours=data.get("operatingHours", ""),
            isActive=data.get("isActive", True),
            createdByStaffId=data.get("createdByStaffId", ""),
            detailsId=str(data.get("_id", "")),
            createdAt=data.get("createdAt"),
        )

    def __repr__(self) -> str:
        return f"<VetDetails clinic={self.clinicName!r} region={self.region!r}>"


# ===========================================================================
# REGIONAL ALERT
# ===========================================================================

class RegionalAlert:
    """
    Represents a time-sensitive health or safety alert for a geographic region.

    Attributes
    ----------
    alertId : str
        MongoDB ``_id`` hex string.
    title : str
    description : str
    region : str
    severity : str
        One of the ``URGENCY_*`` constants.
    isActive : bool
        ``True`` while the alert is current.
    createdBy : str
        ``_id`` of the ``AssociationStaff`` member who created the alert.
    """

    def __init__(
        self,
        title:       str,
        description: str,
        region:      str,
        severity:    str  = URGENCY_URGENT,
        isActive:    bool = True,
        createdBy:   str  = "",
        alertId:     str  = "",
        createdAt:   datetime | None = None,
    ) -> None:
        """
        Initialise a ``RegionalAlert``.

        Parameters
        ----------
        title : str
        description : str
        region : str
        severity : str, optional
        isActive : bool, optional
        createdBy : str, optional
        alertId : str, optional
        createdAt : datetime, optional
        """
        _requireNonEmpty(title,       "title")
        _requireNonEmpty(description, "description")
        _requireNonEmpty(region,      "region")

        if severity not in VALID_URGENCY:
            raise ValueError(f"Invalid severity '{severity}'. Must be one of {VALID_URGENCY}.")

        self.alertId     = alertId
        self.title       = title.strip()
        self.description = description.strip()
        self.region      = region.strip()
        self.severity    = severity
        self.isActive    = bool(isActive)
        self.createdBy   = createdBy
        self.createdAt   = createdAt or datetime.now(timezone.utc)

    def toDict(self) -> dict:
        """
        Serialise ``RegionalAlert`` to a dict.

        Returns
        -------
        dict
        """
        return {
            "title":       self.title,
            "description": self.description,
            "region":      self.region,
            "severity":    self.severity,
            "isActive":    self.isActive,
            "createdBy":   self.createdBy,
            "createdAt":   self.createdAt,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "RegionalAlert":
        """
        Construct a ``RegionalAlert`` from a MongoDB document dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        RegionalAlert
        """
        return cls(
            title       = data.get("title",       ""),
            description = data.get("description", ""),
            region      = data.get("region",      ""),
            severity    = data.get("severity",    URGENCY_URGENT),
            isActive    = data.get("isActive",    True),
            createdBy   = data.get("createdBy",   ""),
            alertId     = str(data.get("_id",     "")),
            createdAt   = data.get("createdAt"),
        )

    def __repr__(self) -> str:
        return f"<RegionalAlert region={self.region!r} severity={self.severity!r} active={self.isActive}>"


# ===========================================================================
# APPROVAL REQUEST
# ===========================================================================

class ApprovalRequest:
    """
    Represents a content submission from a ``VeterinaryPartner`` awaiting
    moderation by ``AssociationStaff``.

    Attributes
    ----------
    requestId : str
    submittedBy : str
        ``_id`` of the submitting ``VeterinaryPartner``.
    contentType : str
        ``"first_aid_guide"`` or ``"instructional_video"``.
    contentData : dict
        The full content payload pending review.
    status : str
        One of ``STATUS_PENDING``, ``STATUS_APPROVED``, ``STATUS_REJECTED``.
    reviewedBy : str
        ``_id`` of the reviewing staff member (empty until reviewed).
    reviewNotes : str
        Moderator feedback notes.
    submittedAt : datetime
    reviewedAt : datetime or None
    """

    CONTENT_TYPE_GUIDE = "first_aid_guide"
    CONTENT_TYPE_VIDEO = "instructional_video"
    VALID_CONTENT_TYPES = {CONTENT_TYPE_GUIDE, CONTENT_TYPE_VIDEO}

    def __init__(
        self,
        submittedBy:  str,
        contentType:  str,
        contentData:  dict,
        status:       str  = STATUS_PENDING,
        reviewedBy:   str  = "",
        reviewNotes:  str  = "",
        requestId:    str  = "",
        submittedAt:  datetime | None = None,
        reviewedAt:   datetime | None = None,
    ) -> None:
        """
        Initialise an ``ApprovalRequest``.

        Parameters
        ----------
        submittedBy : str
        contentType : str
        contentData : dict
        status : str, optional
        reviewedBy : str, optional
        reviewNotes : str, optional
        requestId : str, optional
        submittedAt : datetime, optional
        reviewedAt : datetime, optional
        """
        _requireNonEmpty(submittedBy, "submittedBy")
        if contentType not in self.VALID_CONTENT_TYPES:
            raise ValueError(
                f"Invalid contentType '{contentType}'. "
                f"Must be one of {self.VALID_CONTENT_TYPES}."
            )
        if not contentData:
            raise ValueError("'contentData' must not be empty.")
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'.")

        self.requestId   = requestId
        self.submittedBy = submittedBy
        self.contentType = contentType
        self.contentData = contentData
        self.status      = status
        self.reviewedBy  = reviewedBy
        self.reviewNotes = reviewNotes.strip()
        self.submittedAt = submittedAt or datetime.now(timezone.utc)
        self.reviewedAt  = reviewedAt

    def toDict(self) -> dict:
        """
        Serialise ``ApprovalRequest`` to a dict.

        Returns
        -------
        dict
        """
        return {
            "submittedBy":  self.submittedBy,
            "contentType":  self.contentType,
            "contentData":  self.contentData,
            "status":       self.status,
            "reviewedBy":   self.reviewedBy,
            "reviewNotes":  self.reviewNotes,
            "submittedAt":  self.submittedAt,
            "reviewedAt":   self.reviewedAt,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "ApprovalRequest":
        """
        Construct an ``ApprovalRequest`` from a MongoDB document dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        ApprovalRequest
        """
        return cls(
            submittedBy = data.get("submittedBy", ""),
            contentType = data.get("contentType", cls.CONTENT_TYPE_GUIDE),
            contentData = data.get("contentData", {}),
            status      = data.get("status",      STATUS_PENDING),
            reviewedBy  = data.get("reviewedBy",  ""),
            reviewNotes = data.get("reviewNotes", ""),
            requestId   = str(data.get("_id",     "")),
            submittedAt = data.get("submittedAt"),
            reviewedAt  = data.get("reviewedAt"),
        )

    def __repr__(self) -> str:
        return (
            f"<ApprovalRequest type={self.contentType!r} "
            f"status={self.status!r} id={self.requestId!r}>"
        )


# ===========================================================================
# EDUCATIONAL QUIZ
# ===========================================================================

class QuizQuestion:
    """
    Represents a single multiple-choice question within an ``EducationalQuiz``.

    Attributes
    ----------
    questionId : str
    questionText : str
    options : list[str]
        Answer options, typically prefixed ``"A."`` through ``"D."``.
    correctAnswer : str
        The key of the correct option (e.g. ``"A"``).
    explanation : str
        Shown to the user after they answer.
    """

    def __init__(
        self,
        questionId:    str,
        questionText:  str,
        options:       list[str],
        correctAnswer: str,
        feedback:QuizFeedback,
    ) -> None:
        """
        Initialise a ``QuizQuestion``.

        Parameters
        ----------
        questionId : str
        questionText : str
        options : list[str]
            Must contain at least two options.
        correctAnswer : str
        explanation : str, optional
        """
        _requireNonEmpty(questionId,   "questionId")
        _requireNonEmpty(questionText, "questionText")
        _requireNonEmpty(correctAnswer,"correctAnswer")

        if not options or len(options) < 2:
            raise ValueError("A quiz question must have at least two answer options.")

        self.questionId    = questionId
        self.questionText  = questionText.strip()
        self.options       = options
        self.correctAnswer = correctAnswer.strip().upper()
        self.feedback   = feedback
        
    def checkAnswer(self, selectedAnswer: str) -> bool:
        return selectedAnswer.strip().upper() == self.correctAnswer
    
    def getFeedback(self) -> str:
        return self.feedback.getExplanation()

    def toDict(self) -> dict:
        """
        Serialise ``QuizQuestion`` to a dict.

        Returns
        -------
        dict
        """
        return {
            "questionId":    self.questionId,
            "questionText":  self.questionText,
            "options":       self.options,
            "correctAnswer": self.correctAnswer,
            "feedback":      self.feedback.toDict(),
        }

    @classmethod
    def fromDict(cls, data: dict) -> "QuizQuestion":
        """
        Construct a ``QuizQuestion`` from a dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        QuizQuestion
        """
        feedbackData = data.get("feedback", {"explanationText": data.get("explanation", "")})
        if isinstance(feedbackData, str):
            feedbackData = {"explanationText": feedbackData}

        return cls(
            questionId    = data.get("questionId",    ""),
            questionText  = data.get("questionText",  ""),
            options       = data.get("options",       ["", ""]),
            correctAnswer = data.get("correctAnswer", ""),
            feedback      = QuizFeedback.fromDict(feedbackData),
        )

    def __repr__(self) -> str:
        return f"<QuizQuestion id={self.questionId!r}>"


class QuizFeedback:
    """
    Represents educational feedback shown after answering a quiz question.
    """

    def __init__(self, explanationText: str):
        _requireNonEmpty(explanationText, "explanationText")
        self.explanationText = explanationText.strip()

    def getExplanation(self) -> str:
        return self.explanationText

    def toDict(self) -> dict:
        return {
            "explanationText": self.explanationText,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "QuizFeedback":
        return cls(
            explanationText=data.get("explanationText", "")
        )

    def __repr__(self) -> str:
        return f"<QuizFeedback explanation={self.explanationText[:30]!r}>"


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
