from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType
from .user import User

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
