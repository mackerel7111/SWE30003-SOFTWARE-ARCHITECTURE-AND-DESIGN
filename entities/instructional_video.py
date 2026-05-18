class InstructionalVideo:
    def __init__(self, video_id, title, youtube_url, duration, animal_tag):
        self.video_id = video_id
        self.title = title
        self.youtube_url = youtube_url
        self.duration = duration  # Duration in seconds
        self.animal_tag = animal_tag  # e.g., "cat", "dog", "rabbit"

    def get_video_metadata(self):
        return{
            "video_id": self.video_id,
            "title": self.title,
            "youtube_url": self.youtube_url,
            "duration": self.duration,
            "animal_tag": self.animal_tag
        }
    
    def get_embed_url(self):
        if "watch?v=" in self.youtube_url:
            video_code = self.youtube_url.split("watch?v=")[-1]
            video_code = video_code.split("&")[0]
            return f"https://www.youtube.com/embed/{video_code}"

        if "youtu.be/" in self.youtube_url:
            video_code = self.youtube_url.split("youtu.be/")[-1]
            video_code = video_code.split("?")[0]
            return f"https://www.youtube.com/embed/{video_code}"

        return self.youtube_url
