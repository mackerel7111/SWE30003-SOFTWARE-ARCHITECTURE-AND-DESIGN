from flask import Flask, redirect, render_template, request, session, url_for

from boundaries.database import Database
from boundaries.web_interface import WebInterface
from controls.alert_broadcaster import AlertBroadcaster
from controls.authentication_manager import AuthenticationManager
from controls.content_moderator import ContentModerator
from controls.content_repository import ContentRepository
from controls.search_engine import SearchEngine
from controls.triage_engine import TriageEngine
from entities.association_staff import AssociationStaff
from entities.pet_owner import PetOwner
from entities.pet_profile import PetProfile
from entities.veterinary_partner import VeterinaryPartner


app = Flask(__name__)
app.secret_key = "pet-first-aid-dev-key"

# Bootstrap: initialise database and seed content
database = Database()
database.connect()
database.seed_data()

authentication_manager = AuthenticationManager(database)
content_repository = ContentRepository()
search_engine = SearchEngine(content_repository)
triage_engine = TriageEngine(search_engine)
alert_broadcaster = AlertBroadcaster()
content_moderator = ContentModerator(content_repository)

web_interface = WebInterface(
    authentication_manager=authentication_manager,
    triage_engine=triage_engine,
    search_engine=search_engine,
    alert_broadcaster=alert_broadcaster,
    content_moderator=content_moderator,
)

# Seed demo user accounts
demo_owner = PetOwner(
    user_id="U001",
    email_address="owner@example.com",
    password=authentication_manager.hash_password("ownerpass"),
    home_location="Kuching",
    phone_number="0123456789",
)
demo_staff = AssociationStaff(
    user_id="U002",
    email_address="staff@example.com",
    password=authentication_manager.hash_password("staffpass"),
    employee_id="E001",
    clearance_level=3,
)
demo_vet = VeterinaryPartner(
    user_id="U003",
    email_address="vet@example.com",
    password=authentication_manager.hash_password("vetpass"),
    vet_id="V001",
    license_number="ML-001",
)

for user in [demo_owner, demo_staff, demo_vet]:
    database.execute_update("add_user", user)

alert_broadcaster.subscribe_pet_owner(demo_owner)


def get_current_user():
    session_id = session.get("session_id")
    if not session_id:
        return None
    return authentication_manager.active_sessions_map.get(session_id)


def require_login():
    if get_current_user() is None:
        return redirect(url_for("login"))
    return None


@app.context_processor
def inject_current_user():
    user = get_current_user()
    return {
        "current_user": user,
        "current_role": user.__class__.__name__ if user else None,
    }


@app.route("/")
def index():
    if get_current_user() is not None:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email_address = request.form.get("email_address", "").strip()
        password = request.form.get("password", "")
        session_id = web_interface.submit_login_credentials(email_address, password)

        if session_id:
            session["session_id"] = session_id
            return redirect(url_for("dashboard"))

        error = "Invalid email or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session_id = session.pop("session_id", None)
    if session_id:
        authentication_manager.logout(session_id)
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    guard = require_login()
    if guard:
        return guard
    return render_template("dashboard.html")


@app.route("/triage", methods=["GET", "POST"])
def triage():
    guard = require_login()
    if guard:
        return guard

    result = None
    error = None

    if request.method == "POST":
        try:
            profile = PetProfile(
                profile_id="P001",
                pet_name=request.form.get("pet_name", "").strip(),
                pet_species=request.form.get("pet_species", "").strip(),
                age=int(request.form.get("age", 0)),
                weight=float(request.form.get("weight", 0)),
            )

            result = web_interface.capture_symptom_input(
                category=request.form.get("category", "").strip(),
                description=request.form.get("description", "").strip(),
                duration=int(request.form.get("duration", 0)),
                pet_profile=profile,
            )
        except ValueError:
            error = "Please enter valid numeric values for age, weight, and duration."

    return render_template("triage.html", result=result, error=error)


@app.route("/search", methods=["GET", "POST"])
def search():
    guard = require_login()
    if guard:
        return guard

    keyword = ""
    guides = None
    clinics = None

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        guides = web_interface.capture_search_input(keyword)
        clinics = search_engine.find_clinics_by_region(keyword)

    return render_template(
        "search.html",
        keyword=keyword,
        guides=guides,
        clinics=clinics,
    )


@app.route("/alerts", methods=["GET", "POST"])
def alerts():
    guard = require_login()
    if guard:
        return guard

    region = ""
    active_alerts = None
    message = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create":
            alert = web_interface.capture_new_alert_input(
                alert_id=request.form.get("alert_id", "").strip(),
                title=request.form.get("title", "").strip(),
                message=request.form.get("message", "").strip(),
                target_region=request.form.get("target_region", "").strip(),
                urgency_level=request.form.get("urgency_level", "Low"),
            )
            message = f"Alert {alert.alert_id} created and saved to database."
            region = alert.target_region

        if action == "fetch":
            region = request.form.get("region", "").strip()

        active_alerts = web_interface.fetch_active_alerts(region)

    return render_template(
        "alerts.html",
        region=region,
        alerts=active_alerts,
        message=message,
    )


@app.route("/submit-content", methods=["GET", "POST"])
def submit_content():
    guard = require_login()
    if guard:
        return guard

    message = None

    if request.method == "POST":
        proposed_data = {
            "content_type": "FirstAidGuide",
            "guide_id": request.form.get("guide_id", "").strip(),
            "emergency_category": request.form.get("emergency_category", "").strip(),
            "steps": request.form.get("steps", "").splitlines(),
            "warnings": request.form.get("warnings", "").splitlines(),
        }
        request_obj = web_interface.capture_vet_content_submission(
            request_id=request.form.get("request_id", "").strip(),
            submitted_by=request.form.get("submitted_by", "").strip(),
            proposed_data=proposed_data,
        )
        message = f"Submission {request_obj.request_id} saved to database and is pending review."

    return render_template("submit_content.html", message=message)


@app.route("/moderation", methods=["GET", "POST"])
def moderation():
    guard = require_login()
    if guard:
        return guard

    message = None

    if request.method == "POST":
        request_id = request.form.get("request_id", "").strip()
        decision = request.form.get("decision", "")
        result = web_interface.capture_moderation_decision(request_id, decision)

        if result:
            message = f"Request {result.request_id} marked as {result.status}."

    requests = content_moderator.fetch_all_requests()
    return render_template("moderation.html", requests=requests, message=message)


if __name__ == "__main__":
    app.run(debug=True)
