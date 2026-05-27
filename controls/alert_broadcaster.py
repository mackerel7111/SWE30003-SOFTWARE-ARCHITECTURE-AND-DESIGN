from datetime import date
from entities.regional_alert import RegionalAlert
from boundaries.database import Database


class AlertBroadcaster:
    def __init__(self):
        self._db = Database()
        self.subscribers_list = []

    def subscribe_pet_owner(self, pet_owner):
        if pet_owner not in self.subscribers_list:
            self.subscribers_list.append(pet_owner)

    def unsubscribe_pet_owner(self, pet_owner):
        if pet_owner in self.subscribers_list:
            self.subscribers_list.remove(pet_owner)

    def create_new_alert(self, alert_id, title, message, target_region, urgency_level):
        alert = RegionalAlert(
            alert_id=alert_id,
            title=title,
            message=message,
            target_region=target_region,
            date_issued=date.today(),
            urgency_level=urgency_level,
        )
        doc = {
            "alert_id":      alert.alert_id,
            "title":         alert.title,
            "message":       alert.message,
            "target_region": alert.target_region.lower(),
            "date_issued":   str(alert.date_issued),
            "urgency_level": alert.urgency_level,
        }
        self._db.insert_alert(doc)
        self.notify_subscribers(alert)
        return alert

    def notify_subscribers(self, alert):
        for pet_owner in self.subscribers_list:
            if pet_owner.home_location.lower() == alert.target_region.lower():
                if hasattr(pet_owner, "receive_alert"):
                    pet_owner.receive_alert(alert)

    def fetch_alerts_by_region(self, region):
        docs = self._db.get_alerts_by_region(region)
        return [
            RegionalAlert(
                alert_id=doc["alert_id"],
                title=doc["title"],
                message=doc["message"],
                target_region=doc["target_region"],
                date_issued=doc["date_issued"],
                urgency_level=doc["urgency_level"],
            )
            for doc in docs
        ]
