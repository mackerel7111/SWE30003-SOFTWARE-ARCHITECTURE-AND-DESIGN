from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType
from .user import User

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
