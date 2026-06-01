from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType

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
