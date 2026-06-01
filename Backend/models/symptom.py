from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType

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
