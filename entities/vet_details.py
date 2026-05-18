class VetDetails:
    def __init__(self, clinic_id, clinic_name, region, operating_hours, opening_hour, closing_hour, google_maps_link,):
        self.clinic_id = clinic_id
        self.clinic_name = clinic_name
        self.region = region
        self.operating_hours = operating_hours
        self.opening_hour = opening_hour
        self.closing_hour = closing_hour
        self.google_maps_link = google_maps_link

    def get_clinic_details(self):
        return {
            "clinic_id": self.clinic_id,
            "clinic_name": self.clinic_name,
            "region": self.region,
            "operating_hours": self.operating_hours,
            "opening_hour": self.opening_hour,
            "closing_hour": self.closing_hour,
            "google_maps_link": self.google_maps_link,
        }

    def check_if_currently_open(self, current_hour):
        return self.opening_hour <= current_hour < self.closing_hour