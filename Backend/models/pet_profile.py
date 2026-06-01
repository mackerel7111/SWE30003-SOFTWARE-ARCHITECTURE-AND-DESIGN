from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType

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
