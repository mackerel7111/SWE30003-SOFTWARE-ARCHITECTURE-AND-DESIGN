from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType

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
