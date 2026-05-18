from datetime import date

class RegionalAlert:
    def __init__ (self, alert_id, title, message, target_region, date_issued, urgency_level):
        self.alert_id = alert_id
        self.title = title
        self.message = message
        self.target_region = target_region
        self.date_issued = date_issued
        self.urgency_level = urgency_level
        
    def get_alert_details(self):
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "target_region": self.target_region,
            "date_issued": self.date_issued,
            "urgency_level": self.urgency_level
        }
        
    def is_expired(self, current_date):
        dates_active = (current_date - self.date_issued).days
        return dates_active > 7  # Assuming alerts are active for 7 days
    
    