from entities.user import User

class PetOwner(User):
    def __init__(self, user_id, email_address, password, home_location, phone_number):
        super().__init__(user_id, email_address, password)
        self.home_location = home_location
        self.phone_number = phone_number
        self.pet_profiles = []

    def add_pet_profile(self, pet_profile):
        self.pet_profiles.append(pet_profile)

    def remove_pet_profile(self, profile_id):
        self.pet_profiles = [
            profile for profile in self.pet_profiles
            if profile.profile_id != profile_id
        ]

    def update_location (self, new_location):
        self.home_location = new_location