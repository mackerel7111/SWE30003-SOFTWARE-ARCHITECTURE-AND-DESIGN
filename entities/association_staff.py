from entities.user import User

class AssociationStaff(User):
    def __init__(self, user_id, email_address, password, employee_id, clearance_level):
        super().__init__(user_id, email_address, password)
        self.clearance_level = clearance_level
        self.employee_id = employee_id

    def update_clearance_level(self, new_clearance_level):
        self.clearance_level = new_clearance_level

    def verify_admin_privileges(self):
        return self.clearance_level>= 3