from entities.approval_request import ApprovalRequest

class ContentModerator:
    def __init__(self, content_repository=None):
        self.pending_queue_list = []
        self.content_repository = content_repository 
        
    def queue_new_submission(self, request_id, submitted_by, proposed_data):
        request = ApprovalRequest(
            request_id=request_id,
            submitted_by=submitted_by,
            proposed_data=proposed_data,
        )

        self.pending_queue_list.append(request)
        return request

    def fetch_pending_requests(self):
        return [
            request
            for request in self.pending_queue_list
            if request.is_pending()
        ]

    def approve_request(self, request_id):
        request = self.find_request_by_id(request_id)

        if request is None:
            return None

        request.mark_approved()

        if self.content_repository is not None:
            content = self.content_repository.create_content_from_submission(
                request.proposed_data
            )

            if content is not None:
                self.content_repository.add_new_content(content)

        return request

    def reject_request(self, request_id):
        request = self.find_request_by_id(request_id)

        if request is None:
            return None

        request.mark_rejected()
        return request

    def find_request_by_id(self, request_id):
        for request in self.pending_queue_list:
            if request.request_id == request_id:
                return request

        return None     
    