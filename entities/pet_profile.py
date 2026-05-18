class PetProfile:
    def __init__(self, profile_id, pet_name, pet_species, age, weight):
        self.profile_id = profile_id
        self.pet_name = pet_name
        self.pet_species = pet_species
        self.age = age
        self.weight = weight
        self.known_allergens = []
    
    def update_weight(self, new_weight):
        if new_weight <= 0:
            raise ValueError("Weight must be a positive value")
        self.weight = new_weight

    def add_known_allergen(self, allergen):
        self.known_allergens.append(allergen)

    def get_profile_summary(self):
        return(
            f"Pet Profile ID: {self.profile_id}\n"
            f"Name: {self.pet_name}\n"
            f"Species: {self.pet_species}\n"
            f"Age: {self.age} years\n"
            f"Weight: {self.weight} kg\n"
            f"Known Allergens: {', '.join(self.known_allergens) if self.known_allergens else 'None'}"
        )