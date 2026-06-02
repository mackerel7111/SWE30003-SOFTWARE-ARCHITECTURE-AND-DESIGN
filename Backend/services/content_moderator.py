import logging
from datetime import datetime, timezone
from Backend.database import Database
from Backend.models import (
    PetOwner, AssociationStaff, VeterinaryPartner, PetProfile,
    FirstAidGuide, InstructionalVideo, VetDetails,
    RegionalAlert, ApprovalRequest, EducationalQuiz, QuizQuestion, QuizFeedback,
    ROLE_PET_OWNER, ROLE_ASSOCIATION_STAFF, ROLE_VET_PARTNER,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
)

logger = logging.getLogger(__name__)


class ContentModerator:
    """
    Control class managing workflows for content verification, vetting loops, 
    and approval queues for material submitted by verified vets.
    """

    def initiateSubmission(self, vetUserId: str, contentType: str, contentDataPayload: dict) -> str:
        """
        Log content submissions into review queues, waiting for internal audits.

        Parameters
        ----------
        vetUserId : str
        contentType : str
        contentDataPayload : dict

        Returns
        -------
        str
            The tracking key identifier string for the generated proposal.
        """
        requestObj = ApprovalRequest(
            submittedBy=vetUserId,
            contentType=contentType,
            contentData=contentDataPayload
        )
        db = Database()
        return db.insertApprovalRequest(requestObj.toDict())

    def getPendingQueue(self) -> list[ApprovalRequest]:
        """
        Fetch all incoming content changes still requiring confirmation.

        Returns
        -------
        list[ApprovalRequest]
        """
        db = Database()
        rawRequests = db.findApprovalRequestsByStatus(STATUS_PENDING)
        return [ApprovalRequest.fromDict(req) for req in rawRequests]

    def processReviewDecision(self, requestId: str, staffUserId: str, finalStatus: str, notes: str = "") -> bool:
        """
        Apply an atomic lifecycle status update to a submission request. If approved, 
        the data is compiled and written out to active content collections.

        Parameters
        ----------
        requestId : str
        staffUserId : str
        finalStatus : str
            Must be either STATUS_APPROVED or STATUS_REJECTED.
        notes : str, optional

        Returns
        -------
        bool
            True if status changes were applied safely; False otherwise.
        """
        if finalStatus not in (STATUS_APPROVED, STATUS_REJECTED):
            raise ValueError(f"Invalid outcome option assignment: {finalStatus}")

        db = Database()
        updatedDoc = db.updateApprovalStatus(requestId, finalStatus, staffUserId, notes)
        if not updatedDoc:
            return False

        # If the content is approved, deploy it to active production tables
        if finalStatus == STATUS_APPROVED:
            contentType = updatedDoc.get("contentType")
            contentData = updatedDoc.get("contentData", {})

            if contentType == "first_aid_guide":
                contentData["isApproved"] = True
                contentData["approvedBy"] = staffUserId
                db.insertFirstAidGuide(contentData)
            elif contentType == "instructional_video":
                contentData["isApproved"] = True
                contentData["viewCount"] = 0
                db.insertVideo(contentData)
                
        return True
