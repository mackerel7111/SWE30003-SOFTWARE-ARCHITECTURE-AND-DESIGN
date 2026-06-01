from __future__ import annotations

from datetime import datetime, timezone
from .common import *
from .common import _requireNonEmpty, _requireType

class VetDetails:
    """
    Represents a veterinary clinic directory record.

    VetDetails is maintained by AssociationStaff and retrieved by region
    when pet owners search for nearby professional help.
    """

    def __init__(
        self,
        clinicName: str,
        licenseNumber: str,
        specialisations: list[str] = None,
        region: str = "",
        contactInfo: dict = None,
        operatingHours: str = "",
        isActive: bool = True,
        createdByStaffId: str = "",
        detailsId: str = "",
        createdAt: datetime | None = None,
    ) -> None:
        _requireNonEmpty(clinicName, "clinicName")
        _requireNonEmpty(licenseNumber, "licenseNumber")

        self.detailsId = detailsId
        self.clinicName = clinicName.strip()
        self.licenseNumber = licenseNumber.strip()
        self.specialisations = specialisations if specialisations is not None else []
        self.region = region.strip()
        self.contactInfo = contactInfo if contactInfo is not None else {}
        self.operatingHours = operatingHours.strip()
        self.isActive = bool(isActive)
        self.createdByStaffId = createdByStaffId
        self.createdAt = createdAt or datetime.now(timezone.utc)
        
    def toDict(self) -> dict:
        return {
            "clinicName": self.clinicName,
            "licenseNumber": self.licenseNumber,
            "specialisations": self.specialisations,
            "region": self.region,
            "contactInfo": self.contactInfo,
            "operatingHours": self.operatingHours,
            "isActive": self.isActive,
            "createdByStaffId": self.createdByStaffId,
            "createdAt": self.createdAt,
        }

    @classmethod
    def fromDict(cls, data: dict) -> "VetDetails":
        return cls(
            clinicName=data.get("clinicName", ""),
            licenseNumber=data.get("licenseNumber", ""),
            specialisations=data.get("specialisations", []),
            region=data.get("region", ""),
            contactInfo=data.get("contactInfo", {}),
            operatingHours=data.get("operatingHours", ""),
            isActive=data.get("isActive", True),
            createdByStaffId=data.get("createdByStaffId", ""),
            detailsId=str(data.get("_id", "")),
            createdAt=data.get("createdAt"),
        )

    def __repr__(self) -> str:
        return f"<VetDetails clinic={self.clinicName!r} region={self.region!r}>"
