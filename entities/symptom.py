class Symptom:
    def __init__(self, category, description, duration):
        self.category = category
        self.description = description
        self.duration = duration

    def get_symptom_details(self):
        return (
            f"Category: {self.category}\n"
            f"Description: {self.description}\n"
            f"Duration: {self.duration} hours"
        )