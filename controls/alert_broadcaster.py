from datetime import date
from entities.regional_alert import RegionalAlert

class AlertBroadcaster:
    def __init__(self):
        self.active_alerts_cache = []
        self.subscribers_list = []
        
    def subscribe_pet_owner(self, pet_owner):
        if pet_owner not in self.subscribers_list:
            self.subscribers_list.append(pet_owner)

    def unsubscribe_pet_owner(self, pet_owner):
        if pet_owner in self.subscribers_list:
            self.subscribers_list.remove(pet_owner)
    
    def create_new_alert(self, alert_id, title, message, target_region, urgency_level):
        alert = RegionalAlert(
            alert_id = alert_id, 
            title = title,
            message = message,
            target_region = target_region,
            date_issued = date.today(),
            urgency_level = urgency_level
        )
        
        self.active_alerts_cache.append(alert)
        self.notify_subscribers(alert)
        return alert
    
    def notify_subscribers(self, alert):
        for pet_owner in self.subscribers_list:
            if pet_owner.home_location.lower() == alert.target_region.lower():
                pet_owner.receive_alert(alert)

    def delete_alert(self, alert_id):
        self.active_alerts_cache = [
            alert
            for alert in self.active_alerts_cache
            if alert.alert_id != alert_id
        ]

    def fetch_alerts_by_region(self, region):
        return [
            alert
            for alert in self.active_alerts_cache
            if alert.target_region.lower() == region.lower()
        ]
