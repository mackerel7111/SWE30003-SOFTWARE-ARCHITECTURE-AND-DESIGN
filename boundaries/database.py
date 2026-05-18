class Database:
    def __init__(self, db_connection_string="in-memory"):
        self.db_connection_string = db_connection_string
        self.connection_status = False

        self.users = []
        self.alert_records = []
        self.approval_requests = []
        self.content_records = []

    def connect(self):
        self.connection_status = True
        return self.connection_status

    def disconnect(self):
        self.connection_status = False
        return self.connection_status

    def execute_query(self, query_type, criteria=None):
        if not self.connection_status:
            raise ConnectionError("Database is not connected.")

        if query_type == "find_user_by_email":
            return self.find_user_by_email(criteria)

        if query_type == "get_all_users":
            return self.users

        if query_type == "get_alerts":
            return self.alert_records

        if query_type == "get_approval_requests":
            return self.approval_requests

        if query_type == "get_content_records":
            return self.content_records

        return None

    def execute_update(self, update_type, data=None):
        if not self.connection_status:
            raise ConnectionError("Database is not connected.")

        if update_type == "add_user":
            self.users.append(data)
            return True

        if update_type == "add_alert":
            self.alert_records.append(data)
            return True

        if update_type == "add_approval_request":
            self.approval_requests.append(data)
            return True

        if update_type == "add_content_record":
            self.content_records.append(data)
            return True

        return False

    def find_user_by_email(self, email_address):
        for user in self.users:
            if user.email_address == email_address:
                return user

        return None
