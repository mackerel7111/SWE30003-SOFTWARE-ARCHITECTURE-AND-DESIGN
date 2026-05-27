from entities.first_aid_guide import FirstAidGuide
from entities.instructional_video import InstructionalVideo
from entities.vet_details import VetDetails
from boundaries.database import Database


class ContentRepository:
    def __init__(self):
        self._db = Database()

    def _build_guide(self, doc):
        guide = FirstAidGuide(
            guide_id=doc["guide_id"],
            emergency_category=doc["emergency_category"],
            step_by_step_instruction=doc["step_by_step_instruction"],
            critical_warnings=doc["critical_warnings"],
        )
        return guide

    def _build_video(self, doc):
        return InstructionalVideo(
            video_id=doc["video_id"],
            title=doc["title"],
            youtube_url=doc["youtube_url"],
            duration=doc["duration"],
            animal_tag=doc["animal_tag"],
        )

    def _build_clinic(self, doc):
        return VetDetails(
            clinic_id=doc["clinic_id"],
            clinic_name=doc["clinic_name"],
            region=doc["region"],
            operating_hours=doc["operating_hours"],
            opening_hour=doc["opening_hour"],
            closing_hour=doc["closing_hour"],
            google_maps_link=doc["google_maps_link"],
        )

    def fetch_first_aid_guides(self, emergency_category=None):
        if emergency_category is None:
            docs = self._db.get_all_guides()
        else:
            docs = self._db.get_guides_by_category(emergency_category)
        return [self._build_guide(doc) for doc in docs]

    def fetch_veterinary_clinics(self, region=None):
        if region is None:
            docs = self._db.get_all_clinics()
        else:
            docs = self._db.get_clinics_by_region(region)
        return [self._build_clinic(doc) for doc in docs]

    def fetch_videos(self, animal_tag=None):
        docs = self._db.get_all_videos()
        videos = [self._build_video(doc) for doc in docs]
        if animal_tag:
            videos = [v for v in videos if v.animal_tag.lower() == animal_tag.lower()]
        return videos

    def fetch_educational_quiz(self):
        return []

    def create_content_from_submission(self, proposed_data):
        content_type = proposed_data.get("content_type")

        if content_type == "FirstAidGuide":
            return FirstAidGuide(
                guide_id=proposed_data.get("guide_id"),
                emergency_category=proposed_data.get("emergency_category"),
                step_by_step_instruction=proposed_data.get("steps", []),
                critical_warnings=proposed_data.get("warnings", []),
            )
        if content_type == "VetDetails":
            return VetDetails(
                clinic_id=proposed_data.get("clinic_id"),
                clinic_name=proposed_data.get("clinic_name"),
                region=proposed_data.get("region"),
                operating_hours=proposed_data.get("operating_hours"),
                opening_hour=proposed_data.get("opening_hour", 0),
                closing_hour=proposed_data.get("closing_hour", 24),
                google_maps_link=proposed_data.get("google_maps_link", ""),
            )
        return None

    def add_new_content(self, content):
        if isinstance(content, FirstAidGuide):
            doc = {
                "guide_id": content.guide_id,
                "emergency_category": content.emergency_category,
                "step_by_step_instruction": content.step_by_step_instruction,
                "critical_warnings": content.critical_warnings,
                "instructional_videos": [],
            }
            return self._db.insert_guide(doc)
        if isinstance(content, VetDetails):
            doc = {
                "clinic_id": content.clinic_id,
                "clinic_name": content.clinic_name,
                "region": content.region.lower(),
                "operating_hours": content.operating_hours,
                "opening_hour": content.opening_hour,
                "closing_hour": content.closing_hour,
                "google_maps_link": content.google_maps_link,
            }
            return self._db.insert_clinic(doc)
        return False

    def remove_content(self, guide_id):
        pass
