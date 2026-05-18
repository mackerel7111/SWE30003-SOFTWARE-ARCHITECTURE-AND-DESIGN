from entities.symptom import Symptom

class WebInterface:
    def __init__(self, authentication_manager, triage_engine, search_engine, alert_broadcaster, content_moderator):
        self.authentication_manager = authentication_manager
        self.triage_engine = triage_engine
        self.search_engine = search_engine
        self.alert_broadcaster = alert_broadcaster
        self.content_moderator = content_moderator
        self.current_session_id = None
        self.active_screen = "Login"
    
    def display_login_form (self):
        self.active_screen = "Login"
        return self.active_screen
    
    def submit_login_credentials(self, email_address, password):
        session_id = self.authentication_manager.login(email_address, password)

        if session_id is None:
            return None

        self.current_session_id = session_id
        self.active_screen = "Dashboard"
        return session_id

    def display_triage_form(self):
        self.active_screen = "Triage"
        return self.active_screen

    def capture_symptom_input(self, category, description, duration, pet_profile):
        symptom = Symptom(
            category=category,
            description=description,
            duration=duration,
        )

        return self.triage_engine.evaluate_symptom(symptom, pet_profile)

    def show_urgency_result(self, triage_result):
        self.active_screen = "Triage Result"
        return triage_result

    def display_search_box(self):
        self.active_screen = "Search"
        return self.active_screen

    def capture_search_input(self, keyword):
        return self.search_engine.search_by_keyword(keyword)

    def render_content_gallery(self, content_items):
        gallery_items = []

        for item in content_items:
            if hasattr(item, "get_guide_content"):
                gallery_items.append(item.get_guide_content())

        return gallery_items

    def fetch_active_alerts(self, region):
        return self.alert_broadcaster.fetch_alerts_by_region(region)

    def show_error_banner(self, message):
        return f"Error: {message}"

    def display_staff_dashboard(self):
        self.active_screen = "Staff Dashboard"
        return self.active_screen

    def capture_new_alert_input(self, alert_id, title, message, target_region, urgency_level):
        return self.alert_broadcaster.create_new_alert(
            alert_id=alert_id,
            title=title,
            message=message,
            target_region=target_region,
            urgency_level=urgency_level,
        )

    def display_vet_dashboard(self):
        self.active_screen = "Vet Dashboard"
        return self.active_screen

    def capture_vet_content_submission(self, request_id, submitted_by, proposed_data):
        return self.content_moderator.queue_new_submission(
            request_id=request_id,
            submitted_by=submitted_by,
            proposed_data=proposed_data,
        )

    def display_moderation_queue(self):
        return self.content_moderator.fetch_pending_requests()

    def capture_moderation_decision(self, request_id, decision):
        if decision == "approve":
            return self.content_moderator.approve_request(request_id)

        if decision == "reject":
            return self.content_moderator.reject_request(request_id)

        return None