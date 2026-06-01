import logging
from datetime import datetime, timezone
from Backend.database import Database
from Backend.models import (
    PetOwner, AssociationStaff, VeterinaryPartner, PetProfile,
    Symptom, FirstAidGuide, InstructionalVideo, VetDetails,
    RegionalAlert, ApprovalRequest, EducationalQuiz, QuizQuestion, QuizFeedback,
    ROLE_PET_OWNER, ROLE_ASSOCIATION_STAFF, ROLE_VET_PARTNER,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
)

logger = logging.getLogger(__name__)


class AlertBroadcaster:
    """
    Control class for creating regional alert records and retrieving active alerts
    by region for database-backed in-app display.
    """

    def distributeNewAlert(self, staffUserId: str, title: str, description: str, region: str, severity: str) -> str:
        """
        Create a regional alert record and persist it for later retrieval by users
        in the affected region.

        Parameters
        ----------
        staffUserId : str
        title : str
        description : str
        region : str
        severity : str

        Returns
        -------
        str
            The identifier key of the broadcast document record.
        """
        alertObj = RegionalAlert(
            title=title,
            description=description,
            region=region,
            severity=severity,
            isActive=True,
            createdBy=staffUserId
        )
        db = Database()
        return db.insertAlert(alertObj.toDict())

    def fetchLocalAlerts(self, region: str) -> list[RegionalAlert]:
        """
        Collect active hazard indicators impacting a particular region.

        Parameters
        ----------
        region : str

        Returns
        -------
        list[RegionalAlert]
        """
        db = Database()
        rawAlerts = db.findActiveAlertsByRegion(region)
        return [RegionalAlert.fromDict(alert) for alert in rawAlerts]
