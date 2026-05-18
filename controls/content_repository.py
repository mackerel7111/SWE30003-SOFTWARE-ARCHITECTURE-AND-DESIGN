from entities.first_aid_guide import FirstAidGuide
from entities.instructional_video import InstructionalVideo
from entities.vet_details import VetDetails

class ContentRepository:
    def __init__(self):
        self.cached_guides = [
            FirstAidGuide(
                guide_id="G001",
                emergency_category="breathing",
                step_by_step_instruction=[
                    "Keep the pet calm and limit movement.",
                    "Move the pet to a cool, well-ventilated area.",
                    "Check whether anything is blocking the airway.",
                    "Contact a veterinarian immediately.",
                ],
                critical_warnings=[
                    "Do not force food or water.",
                    "Do not delay professional help if breathing difficulty continues.",
                ],
            ),
            FirstAidGuide(
                guide_id="G002",
                emergency_category="bleeding",
                step_by_step_instruction=[
                    "Apply gentle pressure to the wound with a clean cloth.",
                    "Keep the pet still to reduce further injury.",
                    "Wrap the area lightly if possible.",
                    "Seek veterinary assistance if bleeding does not stop.",
                ],
                critical_warnings=[
                    "Do not remove deeply embedded objects.",
                    "Do not apply a tight tourniquet unless instructed by a vet.",
                ],
            ),
            FirstAidGuide(
                guide_id="G003",
                emergency_category="vomiting",
                step_by_step_instruction=[
                    "Remove food temporarily and observe the pet closely.",
                    "Offer small amounts of clean water if the pet can drink safely.",
                    "Check for repeated vomiting, weakness, or blood.",
                    "Contact a veterinarian if symptoms continue or worsen.",
                ],
                critical_warnings=[
                    "Do not give human medication.",
                    "Seek urgent help if vomiting includes blood or severe weakness.",
                ],
            ),
            FirstAidGuide(
                guide_id="G004",
                emergency_category="limping",
                step_by_step_instruction=[
                    "Limit the pet's movement.",
                    "Check the paw or limb for visible injury.",
                    "Avoid forcing the pet to walk.",
                    "Arrange a vet check if limping persists.",
                ],
                critical_warnings=[
                    "Do not pull or twist the injured limb.",
                    "Do not give painkillers unless prescribed by a vet.",
                ],
            ),
        ]

        self.cached_videos = [
            InstructionalVideo(
                video_id="V001",
                title="Helping a Pet With Breathing Difficulty",
                youtube_url="https://youtu.be/MVndPT9seFE?si=rFJR7ohsa5AGulZ4",
                duration="4:20",
                animal_tag="Cat"
            ),
            InstructionalVideo(
                video_id="V002",
                title="Basic Pet Wound Care",
                youtube_url="https://www.youtube.com/watch?v=MVndPT9seFE",
                duration="3:45",
                animal_tag="Dog"
            ),
        ]
        
        self.cached_clinics = [
            VetDetails(
                clinic_id="C001",
                clinic_name="Happy Paws Veterinary Clinic",
                region="Kuching",
                operating_hours="9:00 AM - 6:00 PM",
                opening_hour=9,
                closing_hour=18,
                google_maps_link="https://maps.google.com"
            ),
            VetDetails(
                clinic_id="C002",
                clinic_name="Emergency Animal Care Centre",
                region="Miri",
                operating_hours="Open 24 hours",
                opening_hour=0,
                closing_hour=24,
                google_maps_link="https://maps.google.com"
            ),
        ]
        self.cached_educational_quiz = []
        
        self.cached_guides[0].add_instructional_video(self.cached_videos[0])
        self.cached_guides[1].add_instructional_video(self.cached_videos[1])

    def fetch_first_aid_guides(self, emergency_category=None):
        if emergency_category is None:
            return self.cached_guides

        return [
            guide
            for guide in self.cached_guides
            if guide.emergency_category.lower() == emergency_category.lower()
        ]

    def fetch_veterinary_clinics(self, region=None):
        if region is None:
            return self.cached_clinics

        return [
            clinic
            for clinic in self.cached_clinics
            if clinic.region.lower() == region.lower()
        ]

    def fetch_videos(self, animal_tag=None):
        if animal_tag is None:
            return self.cached_videos
        return[
            video 
            for video in self.cached_videos
            if video.animal_tag.lower() == animal_tag.lower()
        ]
            
    def fetch_educational_quiz(self):
        return self.cached_educational_quiz

        
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
                opening_hour=proposed_data.get("opening_hour"),
                closing_hour=proposed_data.get("closing_hour"),
                google_maps_link=proposed_data.get("google_maps_link"),
            )
        return None
    
    def add_new_content(self, content):
        if isinstance(content, FirstAidGuide):
            self.cached_guides.append(content)
            return True
        if isinstance(content, VetDetails):
            self.cached_clinics.append(content)
            return True
        return False


    def remove_content(self, guide_id):
        self.cached_guides = [
            guide for guide in self.cached_guides if guide.guide_id != guide_id
        ]
