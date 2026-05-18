from entities.user import User

class VeterinaryPartner(User):
    def __init__(self, user_id, email_address, password, vet_id, license_number):
        super().__init__(user_id, email_address, password)
        self.vet_id = vet_id
        self.license_number = license_number

    def submit_content(self, proposed_data):
        return{
            "submitted by": self.vet_id,
            "proposed_data": proposed_data,
            "status": "Pending"
        }