class SearchEngine:
    def __init__(self, content_repository):
        self.content_repository = content_repository
        self.search_history = []

    def search_by_keyword(self, keyword):
        self.search_history.append(keyword)
        keyword = keyword.lower()

        matching_guides = []
        for guide in self.content_repository.fetch_first_aid_guides():
            category_match = keyword in guide.emergency_category.lower()
            steps_match = any(
                keyword in step.lower()
                for step in guide.step_by_step_instruction
            )
            warnings_match = any(
                keyword in warning.lower()
                for warning in guide.critical_warnings
            )

            if category_match or steps_match or warnings_match:
                matching_guides.append(guide)

        return matching_guides

    def browse_by_category(self, category):
        return self.content_repository.fetch_first_aid_guides(category)

    def fetch_triage_guide(self, symptom):
        matching_guides = self.browse_by_category(symptom.category)

        if matching_guides:
            return matching_guides[0]

        return None

    def find_clinics_by_region(self, region):
        return self.content_repository.fetch_veterinary_clinics(region)
