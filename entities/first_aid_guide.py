from entities.instructional_video import InstructionalVideo

class FirstAidGuide:
    def __init__(
        self,
        guide_id,
        emergency_category,
        step_by_step_instruction,
        critical_warnings,
    ):
        self.guide_id = guide_id
        self.emergency_category = emergency_category
        self.step_by_step_instruction = step_by_step_instruction
        self.critical_warnings = critical_warnings
        self.instructional_videos = []

    def add_instructional_video(self, instructional_video):
        self.instructional_videos.append(instructional_video)

    def get_guide_content(self):
        return {
            "guide_id": self.guide_id,
            "emergency_category": self.emergency_category,
            "step_by_step_instruction": self.step_by_step_instruction,
            "critical_warnings": self.critical_warnings,
            "instructional_videos": [
                video.get_video_metadata() 
                for video in self.instructional_videos
            ],
        }
    
    def get_instructional_videos(self):
        return self.instructional_videos
    

        