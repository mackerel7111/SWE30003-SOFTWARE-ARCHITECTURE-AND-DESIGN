class TriageEngine:
    def __init__(self, search_engine=None):
        self.search_engine = search_engine
        self.active_rule_set = {
            "breathing": "High",
            "bleeding": "High",
            "seizure": "High",
            "vomiting": "Medium",
            "diarrhea": "Medium",
            "limping": "Low",
            "itching": "Low",
        }

    def evaluate_symptom(self, symptom, pet_profile):
        urgency_level = self.determine_urgency_level(symptom)
        first_aid_guide = self.get_first_aid_guide(symptom)

        return {
            "pet_name": pet_profile.pet_name,
            "species": pet_profile.pet_species,
            "symptom_category": symptom.category,
            "symptom_description": symptom.description,
            "duration": symptom.duration,
            "urgency_level": urgency_level,
            "should_escalate_to_vet": self.escalate_to_vet(urgency_level),
            "first_aid_guide": (
                first_aid_guide.get_guide_content()
                if first_aid_guide is not None
                else None
            ),
        }

    def determine_urgency_level(self, symptom):
        category = symptom.category.lower()

        if category in self.active_rule_set:
            return self.active_rule_set[category]

        if symptom.duration >= 24:
            return "Medium"

        return "Low"

    def escalate_to_vet(self, urgency_level):
        return urgency_level == "High"

    def get_first_aid_guide(self, symptom):
        if self.search_engine is None:
            return None

        return self.search_engine.fetch_triage_guide(symptom)
