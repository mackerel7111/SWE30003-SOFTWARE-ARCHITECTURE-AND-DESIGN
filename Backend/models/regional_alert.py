from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType

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
