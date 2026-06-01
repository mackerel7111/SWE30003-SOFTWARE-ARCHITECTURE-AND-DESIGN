"""
Shared constants and validation helpers for the domain/entity layer.
"""

from __future__ import annotations

import re
from typing import Any

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
