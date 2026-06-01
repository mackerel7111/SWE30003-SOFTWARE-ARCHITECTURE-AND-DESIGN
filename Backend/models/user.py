from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType

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
