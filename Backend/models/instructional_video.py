from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType

class InstructionalVideo:
    """
    Represents an instructional video resource linked to a first aid topic.

    Attributes
    ----------
    videoId : str
        MongoDB ``_id`` hex string.
    title : str
    species : str
    url : str
        Publicly accessible video URL.
    durationSeconds : int
        Video length in seconds.
    description : str
    uploadedBy : str
        ``_id`` of the uploading ``VeterinaryPartner``.
    isApproved : bool
    viewCount : int
        Monotonically incremented view counter (updated atomically in DAL).
    tags : list[str]
    """

    def __init__(
        self,
        title:           str,
        species:         str,
        url:             str,
        durationSeconds: int        = 0,
        description:     str        = "",
        uploadedBy:      str        = "",
        isApproved:      bool       = False,
        viewCount:       int        = 0,
        tags:            list[str]  = None,
        videoId:         str        = "",
        uploadedAt:      datetime | None = None,
    ) -> None:
        """
        Initialise an ``InstructionalVideo``.

        Parameters
        ----------
        title : str
        species : str
        url : str
        durationSeconds : int, optional
        description : str, optional
        uploadedBy : str, optional
        isApproved : bool, optional
        viewCount : int, optional
        tags : list[str], optional
        videoId : str, optional
        uploadedAt : datetime, optional
        """
        _requireNonEmpty(title,   "title")
        _requireNonEmpty(species, "species")
        _requireNonEmpty(url,     "url")

        if species.lower() not in VALID_SPECIES:
            raise ValueError(f"Invalid species '{species}'.")
        if durationSeconds < 0:
            raise ValueError("'durationSeconds' cannot be negative.")

        self.videoId         = videoId
        self.title           = title.strip()
        self.species         = species.lower()
        self.url             = url.strip()
        self.durationSeconds = int(durationSeconds)
        self.description     = description.strip()
        self.uploadedBy      = uploadedBy
        self.isApproved      = bool(isApproved)
        self.viewCount       = max(0, int(viewCount))
        self.tags            = tags if tags is not None else []
        self.uploadedAt      = uploadedAt or datetime.now(timezone.utc)

    def toDict(self) -> dict:
        """
        Serialise ``InstructionalVideo`` to a dict.

        Returns
        -------
        dict
        """
        return {
            "title":           self.title,
            "species":         self.species,
            "url":             self.url,
            "durationSeconds": self.durationSeconds,
            "description":     self.description,
            "uploadedBy":      self.uploadedBy,
            "isApproved":      self.isApproved,
            "viewCount":       self.viewCount,
            "tags":            self.tags,
            "uploadedAt":      self.uploadedAt,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "InstructionalVideo":
        """
        Construct an ``InstructionalVideo`` from a MongoDB document dict.

        Parameters
        ----------
        data : dict

        Returns
        -------
        InstructionalVideo
        """
        return cls(
            title           = data.get("title",           ""),
            species         = data.get("species",         SPECIES_DOG),
            url             = data.get("url",             ""),
            durationSeconds = data.get("durationSeconds", 0),
            description     = data.get("description",     ""),
            uploadedBy      = data.get("uploadedBy",      ""),
            isApproved      = data.get("isApproved",      False),
            viewCount       = data.get("viewCount",       0),
            tags            = data.get("tags",            []),
            videoId         = str(data.get("_id",         "")),
            uploadedAt      = data.get("uploadedAt"),
        )

    def __repr__(self) -> str:
        return f"<InstructionalVideo title={self.title!r} species={self.species!r}>"
