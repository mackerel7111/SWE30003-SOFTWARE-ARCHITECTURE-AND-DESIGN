from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType
from .user import User

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
