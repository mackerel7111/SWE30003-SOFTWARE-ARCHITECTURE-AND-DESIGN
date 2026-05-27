from types import SimpleNamespace

from flask import Flask, redirect, render_template, request, session, url_for

from Backend.database import Database
from Backend.models import (
    PetProfile,
    ROLE_ASSOCIATION_STAFF,
    ROLE_PET_OWNER,
    ROLE_VET_PARTNER,
    STATUS_APPROVED,
    STATUS_REJECTED,
    URGENCY_EMERGENCY,
    URGENCY_NON_URGENT,
    URGENCY_URGENT,
)
from Backend.services import (
    AlertBroadcaster,
    AuthenticationManager,
    ContentRepository,
    ContentModerator,
    SearchEngine,
    TriageEngine,
)


app = Flask(__name__)
app.secret_key = "pet-first-aid-dev-key"

database = Database()
database.seed_data()

authentication_manager = AuthenticationManager()
search_engine = SearchEngine()
triage_engine = TriageEngine()
alert_broadcaster = AlertBroadcaster()
content_moderator = ContentModerator()
content_repository = ContentRepository()

ROLE_LABELS = {
    ROLE_PET_OWNER: "PetOwner",
    ROLE_ASSOCIATION_STAFF: "AssociationStaff",
    ROLE_VET_PARTNER: "VeterinaryPartner",
}

URGENCY_FROM_FORM = {
    "Low": URGENCY_NON_URGENT,
    "Medium": URGENCY_URGENT,
    "High": URGENCY_EMERGENCY,
}

URGENCY_TO_TEMPLATE = {
    URGENCY_NON_URGENT: "Low",
    URGENCY_URGENT: "Medium",
    URGENCY_EMERGENCY: "High",
}

DEMO_LOGIN_ALIASES = {
    ("owner@example.com", "ownerpass"): ("owner@example.com", "owner_password"),
    ("staff@example.com", "staffpass"): ("admin@petfirstaid.org", "admin_password"),
    ("vet@example.com", "vetpass"): ("dr.tan@vetclinic.com", "vet1_password"),
}


def get_current_user():
    user = session.get("user")
    if not user:
        return None

    return SimpleNamespace(
        user_id=user.get("userId"),
        email_address=user.get("email"),
        full_name=user.get("fullName"),
        role=user.get("role"),
    )


def get_current_role():
    user = session.get("user")
    if not user:
        return None
    return ROLE_LABELS.get(user.get("role"))


def require_login():
    if get_current_user() is None:
        return redirect(url_for("login"))
    return None


def current_session_user():
    return session.get("user")


def require_role(*allowed_roles):
    guard = require_login()
    if guard:
        return guard

    session_user = current_session_user()
    if session_user.get("role") not in allowed_roles:
        return redirect(url_for("dashboard"))

    return None


def form_text(field_name, default=""):
    return request.form.get(field_name, default).strip()


def guide_for_template(guide):
    warnings = []
    if guide.warningNotes:
        warnings = [note.strip() for note in guide.warningNotes.splitlines() if note.strip()]
        if not warnings:
            warnings = [guide.warningNotes]

    return SimpleNamespace(
        guide_id=guide.guideId,
        emergency_category=guide.title,
        step_by_step_instruction=guide.steps,
        critical_warnings=warnings,
        urgency_level=URGENCY_TO_TEMPLATE.get(guide.urgencyLevel, guide.urgencyLevel),
    )


def clinic_for_template(clinic):
    contact_info = clinic.contactInfo or {}

    return SimpleNamespace(
        clinic_id=clinic.detailsId,
        clinic_name=clinic.clinicName,
        region=clinic.region,
        operating_hours=clinic.operatingHours,
        google_maps_link=contact_info.get("mapsLink") or contact_info.get("googleMapsLink") or "#",
    )


def video_for_template(video):
    minutes, seconds = divmod(video.durationSeconds, 60)
    duration = f"{minutes}:{seconds:02d}" if video.durationSeconds else "N/A"

    return SimpleNamespace(
        video_id=video.videoId,
        title=video.title,
        species=video.species.title(),
        url=video.url,
        duration=duration,
        description=video.description,
        tags=", ".join(video.tags) or "None",
    )


def alert_for_template(alert):
    return SimpleNamespace(
        alert_id=alert.alertId,
        title=alert.title,
        message=alert.description,
        target_region=alert.region,
        urgency_level=URGENCY_TO_TEMPLATE.get(alert.severity, alert.severity),
        date_issued=alert.createdAt,
    )


def request_for_template(approval_request):
    status = approval_request.status.capitalize()
    proposed_data = approval_request.contentData or {}
    is_video = approval_request.contentType == "instructional_video"
    warning_notes = proposed_data.get("warningNotes", "")
    warnings = [
        note.strip()
        for note in warning_notes.splitlines()
        if note.strip()
    ]

    return SimpleNamespace(
        request_id=approval_request.requestId,
        submitted_by=approval_request.submittedBy,
        content_type=approval_request.contentType.replace("_", " ").title(),
        is_video=is_video,
        title=proposed_data.get("title", "Untitled submission"),
        species=proposed_data.get("species", "N/A").title(),
        urgency_level=URGENCY_TO_TEMPLATE.get(
            proposed_data.get("urgencyLevel"),
            proposed_data.get("urgencyLevel", "N/A"),
        ),
        keywords=", ".join(proposed_data.get("keywords", proposed_data.get("tags", []))) or "None",
        steps=proposed_data.get("steps", []),
        warnings=warnings,
        url=proposed_data.get("url", ""),
        duration_seconds=proposed_data.get("durationSeconds", 0),
        description=proposed_data.get("description", ""),
        tags=", ".join(proposed_data.get("tags", [])) or "None",
        submitted_at=approval_request.submittedAt,
        status=status,
    )


def pet_for_template(pet):
    return SimpleNamespace(
        pet_id=pet.petId,
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        age=pet.age,
        weight_kg=pet.weightKg,
        medical_history=", ".join(pet.medicalHistory),
        emergency_notes=pet.emergencyNotes,
    )


def quiz_for_template(quiz):
    return SimpleNamespace(
        quiz_id=quiz.quizId,
        title=quiz.title,
        topic=quiz.topic,
        difficulty_level=quiz.difficultyLevel,
        questions=quiz.questions,
        question_count=quiz.questionCount,
    )


@app.context_processor
def inject_current_user():
    return {
        "current_user": get_current_user(),
        "current_role": get_current_role(),
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
        email_address = form_text("email_address")
        password = request.form.get("password", "")
        auth_email, auth_password = DEMO_LOGIN_ALIASES.get(
            (email_address, password),
            (email_address, password),
        )
        session_user = authentication_manager.authenticateUser(auth_email, auth_password)

        if session_user:
            session["user"] = session_user
            return redirect(url_for("dashboard"))

        error = "Invalid email or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    guard = require_login()
    if guard:
        return guard
    return render_template("dashboard.html")


@app.route("/pets", methods=["GET", "POST"])
def pets():
    guard = require_role(ROLE_PET_OWNER)
    if guard:
        return guard

    message = None
    error = None
    session_user = current_session_user()

    if request.method == "POST":
        try:
            medical_history = [
                note.strip()
                for note in request.form.get("medical_history", "").splitlines()
                if note.strip()
            ]
            pet_profile = PetProfile(
                ownerId=session_user["userId"],
                name=form_text("name"),
                species=form_text("species").lower(),
                breed=form_text("breed"),
                age=int(request.form.get("age", 0)),
                weightKg=float(request.form.get("weight_kg", 0)),
                sex=form_text("sex").lower(),
                isNeutered=request.form.get("is_neutered") == "yes",
                medicalHistory=medical_history,
                emergencyNotes=form_text("emergency_notes"),
            )
            pet_id = database.insertPetProfile(pet_profile.toDict())
            message = f"Pet profile {pet_id} saved."
        except ValueError as err:
            error = str(err)

    saved_pets = [
        pet_for_template(PetProfile.fromDict(pet))
        for pet in database.findPetsByOwner(session_user["userId"])
    ]

    return render_template(
        "pets.html",
        pets=saved_pets,
        message=message,
        error=error,
    )


@app.route("/triage", methods=["GET", "POST"])
def triage():
    guard = require_role(ROLE_PET_OWNER)
    if guard:
        return guard

    result = None
    error = None
    session_user = current_session_user()
    saved_pets = [
        pet_for_template(PetProfile.fromDict(pet))
        for pet in database.findPetsByOwner(session_user["userId"])
    ]

    if request.method == "POST":
        try:
            pet_id = form_text("pet_id")
            pet_document = database.findPetById(pet_id)
            if not pet_document or pet_document.get("ownerId") != session_user["userId"]:
                raise ValueError("Please select a valid saved pet profile.")

            pet_profile = PetProfile.fromDict(pet_document)
            symptom_category = form_text("category")
            description = form_text("description")
            duration = int(request.form.get("duration", 0))

            assessment = triage_engine.evaluateSymptoms(pet_profile.species, [symptom_category])
            matched_guides = search_engine.queryFirstAidGuides(pet_profile.species, symptom_category)

            database.insertSymptomRecord({
                "petId": pet_profile.petId,
                "symptoms": [symptom_category],
                "description": description,
                "durationHours": duration,
                "urgencyLevel": assessment.get("urgencyLevel"),
                "triageNotes": assessment.get("triageNotes"),
            })

            urgency_level = URGENCY_TO_TEMPLATE.get(
                assessment.get("urgencyLevel"),
                assessment.get("urgencyLevel", "Low"),
            )

            result = SimpleNamespace(
                pet_name=pet_profile.name,
                species=pet_profile.species,
                symptom_category=symptom_category,
                urgency_level=urgency_level,
                should_escalate_to_vet=assessment.get("urgencyLevel") != URGENCY_NON_URGENT,
                first_aid_guide=guide_for_template(matched_guides[0]) if matched_guides else None,
            )
        except ValueError:
            error = "Please enter valid numeric values for age, weight, and duration."

    return render_template(
        "triage.html",
        pets=saved_pets,
        result=result,
        error=error,
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    guard = require_role(ROLE_PET_OWNER)
    if guard:
        return guard

    keyword = ""
    search_type = "guide"
    guides = None
    clinics = None
    videos = None

    if request.method == "POST":
        keyword = form_text("keyword")
        search_type = request.form.get("search_type", "guide")

        if search_type == "guide":
            matched_guides = []
            for species in ["dog", "cat", "rabbit", "other"]:
                matched_guides.extend(search_engine.queryFirstAidGuides(species, keyword))

            guides = [guide_for_template(guide) for guide in matched_guides]

        if search_type == "clinic":
            clinics = [
                clinic_for_template(clinic)
                for clinic in search_engine.searchVetsByRegion(keyword)
            ]

        if search_type == "video":
            videos = [
                video_for_template(video)
                for video in content_repository.getApprovedVideos(keyword.lower())
            ]

    return render_template(
        "search.html",
        keyword=keyword,
        search_type=search_type,
        guides=guides,
        clinics=clinics,
        videos=videos,
    )


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    guard = require_role(ROLE_PET_OWNER)
    if guard:
        return guard

    quizzes = [quiz_for_template(quiz) for quiz in content_repository.getAllQuizzes()]
    selected_quiz = None
    result = None
    error = None

    selected_quiz_id = request.form.get("quiz_id") or request.args.get("quiz_id")
    if not selected_quiz_id and quizzes:
        selected_quiz_id = quizzes[0].quiz_id

    if selected_quiz_id:
        quiz_obj = content_repository.getQuizDetails(selected_quiz_id)
        if quiz_obj:
            selected_quiz = quiz_for_template(quiz_obj)
        else:
            error = "Selected quiz could not be found."

    if request.method == "POST" and selected_quiz:
        submitted_answers = {
            question.questionId: request.form.get(question.questionId, "")
            for question in selected_quiz.questions
        }
        result = content_repository.submitQuizResults(
            selected_quiz.quiz_id,
            submitted_answers,
        )

    return render_template(
        "quiz.html",
        quizzes=quizzes,
        selected_quiz=selected_quiz,
        result=result,
        error=error,
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
        session_user = current_session_user()

        if action == "create":
            if session_user.get("role") != ROLE_ASSOCIATION_STAFF:
                return redirect(url_for("dashboard"))

            title = form_text("title")
            description = form_text("message")
            region = form_text("target_region")
            severity = URGENCY_FROM_FORM.get(
                request.form.get("urgency_level", "Low"),
                URGENCY_NON_URGENT,
            )

            alert_id = alert_broadcaster.distributeNewAlert(
                staffUserId=session_user["userId"],
                title=title,
                description=description,
                region=region,
                severity=severity,
            )
            message = f"Alert {alert_id} created and saved to database."

        if action == "fetch":
            region = form_text("region")

        active_alerts = [
            alert_for_template(alert)
            for alert in alert_broadcaster.fetchLocalAlerts(region)
        ]

    return render_template(
        "alerts.html",
        region=region,
        alerts=active_alerts,
        message=message,
    )


@app.route("/submit-content", methods=["GET", "POST"])
def submit_content():
    guard = require_role(ROLE_VET_PARTNER)
    if guard:
        return guard

    message = None

    if request.method == "POST":
        session_user = current_session_user()
        content_type = request.form.get("content_type", "first_aid_guide")

        if content_type == "instructional_video":
            tags = [
                tag.strip().lower()
                for tag in request.form.get("video_tags", "").split(",")
                if tag.strip()
            ]
            content_data = {
                "title": form_text("video_title"),
                "species": form_text("video_species", "dog").lower(),
                "url": form_text("video_url"),
                "durationSeconds": int(request.form.get("duration_seconds", 0)),
                "description": form_text("video_description"),
                "uploadedBy": session_user["userId"],
                "viewCount": 0,
                "tags": tags,
            }
        else:
            emergency_category = form_text("emergency_category")
            steps = [
                step.strip()
                for step in request.form.get("steps", "").splitlines()
                if step.strip()
            ]
            warnings = [
                warning.strip()
                for warning in request.form.get("warnings", "").splitlines()
                if warning.strip()
            ]

            content_data = {
                "title": emergency_category.title(),
                "species": form_text("guide_species", "dog").lower(),
                "urgencyLevel": URGENCY_NON_URGENT,
                "keywords": [emergency_category.lower()],
                "steps": steps,
                "warningNotes": "\n".join(warnings),
            }

        request_id = content_moderator.initiateSubmission(
            vetUserId=session_user["userId"],
            contentType=content_type,
            contentDataPayload=content_data,
        )
        message = f"Submission {request_id} saved to database and is pending review."

    return render_template("submit_content.html", message=message)


@app.route("/moderation", methods=["GET", "POST"])
def moderation():
    guard = require_role(ROLE_ASSOCIATION_STAFF)
    if guard:
        return guard

    message = None

    if request.method == "POST":
        session_user = current_session_user()
        request_id = form_text("request_id")
        decision = request.form.get("decision", "")
        final_status = STATUS_APPROVED if decision == "approve" else STATUS_REJECTED

        success = content_moderator.processReviewDecision(
            requestId=request_id,
            staffUserId=session_user["userId"],
            finalStatus=final_status,
        )

        if success:
            message = f"Request {request_id} marked as {final_status.capitalize()}."

    requests = [
        request_for_template(approval_request)
        for approval_request in content_moderator.getPendingQueue()
    ]
    return render_template("moderation.html", requests=requests, message=message)


if __name__ == "__main__":
    app.run(debug=True)
