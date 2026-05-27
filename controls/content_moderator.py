from entities.approval_request import ApprovalRequest
from boundaries.database import Database


class ContentModerator:
    def __init__(self, content_repository=None):
        self.content_repository = content_repository
        self._db = Database()

    def queue_new_submission(self, request_id, submitted_by, proposed_data):
        request = ApprovalRequest(
            request_id=request_id,
            submitted_by=submitted_by,
            proposed_data=proposed_data,
        )
        doc = {
            "request_id":    request.request_id,
            "submitted_by":  request.submitted_by,
            "proposed_data": request.proposed_data,
            "submission_date": str(request.submission_date),
            "status":        request.status,
        }
        self._db.insert_approval_request(doc)
        return request

    def fetch_pending_requests(self):
        docs = self._db.get_pending_approval_requests()
        return [
            ApprovalRequest(
                request_id=doc["request_id"],
                submitted_by=doc["submitted_by"],
                proposed_data=doc["proposed_data"],
                status=doc["status"],
            )
            for doc in docs
        ]

    def fetch_all_requests(self):
        docs = self._db.get_all_approval_requests()
        return [
            ApprovalRequest(
                request_id=doc["request_id"],
                submitted_by=doc["submitted_by"],
                proposed_data=doc["proposed_data"],
                status=doc["status"],
            )
            for doc in docs
        ]

    def approve_request(self, request_id):
        self._db.update_approval_request_status(request_id, "Approved")

        docs = self._db.get_all_approval_requests()
        target_doc = next((d for d in docs if d["request_id"] == request_id), None)
        if target_doc is None:
            return None

        request = ApprovalRequest(
            request_id=target_doc["request_id"],
            submitted_by=target_doc["submitted_by"],
            proposed_data=target_doc["proposed_data"],
            status="Approved",
        )

        if self.content_repository is not None:
            content = self.content_repository.create_content_from_submission(
                target_doc["proposed_data"]
            )
            if content is not None:
                self.content_repository.add_new_content(content)

        return request

    def reject_request(self, request_id):
        self._db.update_approval_request_status(request_id, "Rejected")

        docs = self._db.get_all_approval_requests()
        target_doc = next((d for d in docs if d["request_id"] == request_id), None)
        if target_doc is None:
            return None

        return ApprovalRequest(
            request_id=target_doc["request_id"],
            submitted_by=target_doc["submitted_by"],
            proposed_data=target_doc["proposed_data"],
            status="Rejected",
        )

    def find_request_by_id(self, request_id):
        docs = self._db.get_all_approval_requests()
        target_doc = next((d for d in docs if d["request_id"] == request_id), None)
        if target_doc is None:
            return None
        return ApprovalRequest(
            request_id=target_doc["request_id"],
            submitted_by=target_doc["submitted_by"],
            proposed_data=target_doc["proposed_data"],
            status=target_doc["status"],
        )
