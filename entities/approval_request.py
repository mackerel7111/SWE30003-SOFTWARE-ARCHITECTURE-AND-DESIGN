from datetime import date

class ApprovalRequest:
    VALID_STATUSES = ["Pending", "Approved", "Rejected"]

    def __init__(self, request_id, submitted_by, proposed_data, submission_date=None, status="Pending"):
        self.request_id = request_id
        self.submitted_by = submitted_by
        self.proposed_data = proposed_data
        self.submission_date = submission_date or date.today()
        self.status = status
        
    def get_request_details (self):
        return{
            "request_id": self.request_id,
            "submitted_by": self.submitted_by,
            "proposed_data": self.proposed_data,
            "submission_date": self.submission_date,
            "status": self.status,
        }
        
    def mark_approved(self):
        self.status = "Approved"

    def mark_rejected(self):
        self.status = "Rejected"

    def is_pending(self):
        return self.status == "Pending"

    def is_approved(self):
        return self.status == "Approved"

    def is_rejected(self):
        return self.status == "Rejected"