from abc import ABC


class User(ABC):
    def __init__(self, user_id, email_address, password):
        self.user_id = user_id
        self.email_address = email_address
        self._password = password

    def update_email(self, new_email):
        self.email_address = new_email

    def reset_password(self, new_password):
        self._password = new_password