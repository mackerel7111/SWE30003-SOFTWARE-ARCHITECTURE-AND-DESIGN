from types import SimpleNamespace

from flask import redirect, render_template, request, session, url_for

from app_context import (
    DEMO_LOGIN_ALIASES,
    QUIZ_TOPICS,
    ROLE_ASSOCIATION_STAFF,
    ROLE_PET_OWNER,
    ROLE_VET_PARTNER,
    STATUS_APPROVED,
    STATUS_REJECTED,
    SUPPORTED_SPECIES,
    URGENCY_FROM_FORM,
    URGENCY_NON_URGENT,
    URGENCY_TO_TEMPLATE,
    URGENCY_URGENT,
    URGENCY_EMERGENCY,
    PetOwner,
    PetProfile,
    VeterinaryPartner,
)
from web.session_helpers import (
    current_session_user,
    form_text,
    get_current_role,
    get_current_user,
    get_current_user_region,
    require_login,
    require_role,
)
from web.template_adapters import (
    alert_for_template,
    clinic_for_template,
    guide_for_template,
    pet_for_template,
    quiz_for_template,
    request_for_template,
    video_for_template,
)


class AppRouting:
    def __init__(
        self,
        app,
        database,
        authenticationManager,
        searchEngine,
        triageEngine,
        alertBroadcaster,
        contentModerator,
        contentRepository,
    ):
        self.app = app
        self.database = database
        self.authenticationManager = authenticationManager
        self.searchEngine = searchEngine
        self.triageEngine = triageEngine
        self.alertBroadcaster = alertBroadcaster
        self.contentModerator = contentModerator
        self.contentRepository = contentRepository

    def registerRoutes(self):
        self.app.context_processor(self.injectCurrentUser)
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/login", "login", self.login, methods=["GET", "POST"])
        self.app.add_url_rule("/register", "register", self.register, methods=["GET", "POST"])
        self.app.add_url_rule("/logout", "logout", self.logout)
        self.app.add_url_rule("/dashboard", "dashboard", self.viewDashboard)
        self.app.add_url_rule("/pets", "pets", self.managePetProfiles, methods=["GET", "POST"])
        self.app.add_url_rule("/triage", "triage", self.evaluateTriage, methods=["GET", "POST"])
        self.app.add_url_rule("/search", "search", self.searchContent, methods=["GET", "POST"])
        self.app.add_url_rule("/quiz", "quiz", self.takeQuiz, methods=["GET", "POST"])
        self.app.add_url_rule("/alerts", "alerts", self.manageAlerts, methods=["GET", "POST"])
        self.app.add_url_rule("/submit-content", "submit_content", self.submitContent, methods=["GET", "POST"])
        self.app.add_url_rule("/moderation", "moderation", self.reviewModerationQueue, methods=["GET", "POST"])
        self.app.add_url_rule("/vet-details", "vet_details", self.manageVetDetails, methods=["GET", "POST"])

    def injectCurrentUser(self):
        return {
            "current_user": get_current_user(),
            "current_role": get_current_role(),
        }

    def index(self):
        if get_current_user() is not None:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    def login(self):
        error = None
        message = request.args.get("message")

        if request.method == "POST":
            email_address = form_text("email_address")
            password = request.form.get("password", "")
            auth_email, auth_password = DEMO_LOGIN_ALIASES.get(
                (email_address, password),
                (email_address, password),
            )
            session_user = self.authenticationManager.authenticateUser(auth_email, auth_password)

            if session_user:
                session["user"] = session_user
                return redirect(url_for("dashboard"))

            error = "Invalid email or password."

        return render_template("login.html", error=error, message=message)

    def register(self):
        if get_current_user() is not None:
            return redirect(url_for("dashboard"))

        error = None

        if request.method == "POST":
            try:
                role = request.form.get("role", ROLE_PET_OWNER)
                email = form_text("email")
                full_name = form_text("full_name")
                password = request.form.get("password", "")
                confirm_password = request.form.get("confirm_password", "")

                if self.database.findUserByEmail(email):
                    raise ValueError("An account with this email already exists.")
                if len(password) < 6:
                    raise ValueError("Password must be at least 6 characters.")
                if password != confirm_password:
                    raise ValueError("Passwords do not match.")

                password_hash = f"hashed_{password}_placeholder"

                if role == ROLE_VET_PARTNER:
                    specialisations = [
                        item.strip()
                        for item in request.form.get("specialisations", "").split(",")
                        if item.strip()
                    ]
                    user = VeterinaryPartner(
                        email=email,
                        fullName=full_name,
                        passwordHash=password_hash,
                        licenseNumber=form_text("license_number"),
                        specialisations=specialisations,
                        isVerified=False,
                    )
                else:
                    user = PetOwner(
                        email=email,
                        fullName=full_name,
                        passwordHash=password_hash,
                        phoneNumber=form_text("phone_number"),
                        region=form_text("region"),
                    )

                self.database.insertUser(user.toDict())
                return redirect(url_for("login", message="Registration successful. Please log in."))
            except ValueError as err:
                error = str(err)

        return render_template("register.html", error=error)

    def logout(self):
        session.clear()
        return redirect(url_for("login"))

    def viewDashboard(self):
        guard = require_login()
        if guard:
            return guard
        return render_template("dashboard.html")

    def managePetProfiles(self):
        guard = require_role(ROLE_PET_OWNER)
        if guard:
            return guard

        message = None
        error = None
        session_user = current_session_user()
        form_mode = request.args.get("mode", "")
        selected_pet = None
        selected_pet_id = request.args.get("pet_id", "")

        if request.method == "POST":
            try:
                action = request.form.get("action", "add")
                medical_history = [
                    note.strip()
                    for note in request.form.get("medical_history", "").splitlines()
                    if note.strip()
                ]
                pet_data = {
                    "name": form_text("name"),
                    "species": form_text("species").lower(),
                    "breed": form_text("breed"),
                    "age": int(request.form.get("age", 0)),
                    "weightKg": float(request.form.get("weight_kg", 0)),
                    "sex": form_text("sex").lower(),
                    "isNeutered": request.form.get("is_neutered") == "yes",
                    "medicalHistory": medical_history,
                    "emergencyNotes": form_text("emergency_notes"),
                }

                if action == "edit":
                    pet_id = form_text("pet_id")
                    existing_pet = self.database.findPetById(pet_id)
                    if not existing_pet or existing_pet.get("ownerId") != session_user["userId"]:
                        raise ValueError("Please select a valid pet profile to edit.")

                    self.database.updatePetProfile(pet_id, pet_data)
                    message = "Pet profile updated."
                else:
                    pet_profile = PetProfile(
                        ownerId=session_user["userId"],
                        **pet_data,
                    )
                    pet_id = self.database.insertPetProfile(pet_profile.toDict())
                    message = f"Pet profile {pet_id} saved."
            except ValueError as err:
                error = str(err)
                form_mode = request.form.get("action", form_mode)
                selected_pet_id = request.form.get("pet_id", selected_pet_id)

        pet_documents = self.database.findPetsByOwner(session_user["userId"])
        saved_pets = [pet_for_template(PetProfile.fromDict(pet)) for pet in pet_documents]

        if form_mode == "edit" and selected_pet_id:
            pet_document = self.database.findPetById(selected_pet_id)
            if pet_document and pet_document.get("ownerId") == session_user["userId"]:
                selected_pet = pet_for_template(PetProfile.fromDict(pet_document))

        return render_template(
            "pets.html",
            pets=saved_pets,
            form_mode=form_mode,
            selected_pet=selected_pet,
            selected_pet_id=selected_pet_id,
            message=message,
            error=error,
        )

    def evaluateTriage(self):
        guard = require_role(ROLE_PET_OWNER)
        if guard:
            return guard

        result = None
        error = None
        session_user = current_session_user()
        saved_region = get_current_user_region()
        saved_pets = [
            pet_for_template(PetProfile.fromDict(pet))
            for pet in self.database.findPetsByOwner(session_user["userId"])
        ]

        if request.method == "POST":
            try:
                pet_id = form_text("pet_id")
                pet_document = self.database.findPetById(pet_id)
                if not pet_document or pet_document.get("ownerId") != session_user["userId"]:
                    raise ValueError("Please select a valid saved pet profile.")

                pet_profile = PetProfile.fromDict(pet_document)
                symptom_category = form_text("category")
                description = form_text("description")
                duration = int(request.form.get("duration", 0))

                assessment = self.triageEngine.evaluateSymptoms(pet_profile.species, [symptom_category])
                matched_guides = self.searchEngine.queryFirstAidGuides(pet_profile.species, symptom_category)

                self.database.insertSymptomRecord({
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
                    should_contact_vet=assessment.get("urgencyLevel") == URGENCY_URGENT,
                    should_seek_emergency_care=assessment.get("urgencyLevel") == URGENCY_EMERGENCY,
                    vet_search_url=url_for(
                        "search",
                        search_type="clinic",
                        keyword=saved_region,
                        auto="1",
                    ),
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

    def searchContent(self):
        guard = require_role(ROLE_PET_OWNER)
        if guard:
            return guard

        keyword = ""
        search_type = "guide"
        guides = None
        clinics = None
        videos = None
        saved_region = get_current_user_region()
        selected_species = "dog"

        if request.method == "GET":
            keyword = request.args.get("keyword", "").strip()
            search_type = request.args.get("search_type", search_type)
            selected_species = request.args.get("species", selected_species)

        if request.method == "POST" or request.args.get("auto") == "1":
            if request.method == "POST":
                keyword = form_text("keyword")
                search_type = request.form.get("search_type", "guide")
                selected_species = request.form.get("species", selected_species)

            if search_type == "guide":
                matched_guides = self.searchEngine.queryFirstAidGuides(selected_species.lower(), keyword)
                guides = [guide_for_template(guide) for guide in matched_guides]

            if search_type == "clinic":
                keyword = keyword or saved_region
                clinics = [
                    clinic_for_template(clinic)
                    for clinic in self.searchEngine.searchVetsByRegion(keyword)
                ]

            if search_type == "video":
                keyword = selected_species
                videos = [
                    video_for_template(video)
                    for video in self.contentRepository.getApprovedVideos(selected_species.lower())
                ]

        return render_template(
            "search.html",
            keyword=keyword,
            search_type=search_type,
            guides=guides,
            clinics=clinics,
            videos=videos,
            saved_region=saved_region,
            selected_species=selected_species,
            supported_species=SUPPORTED_SPECIES,
        )

    def takeQuiz(self):
        guard = require_role(ROLE_PET_OWNER)
        if guard:
            return guard

        selected_species = request.values.get("species", "dog")
        selected_topic = request.values.get("topic", "breathing")
        selected_quiz_id = request.form.get("quiz_id") or request.args.get("quiz_id")
        should_show_available_quizzes = (
            request.method == "POST"
            or "species" in request.args
            or "topic" in request.args
            or bool(selected_quiz_id)
        )
        quizzes = []
        if should_show_available_quizzes:
            quizzes = [
                quiz_for_template(quiz)
                for quiz in self.contentRepository.getAllQuizzes()
                if quiz.species == selected_species and quiz.topic == selected_topic
            ]
        selected_quiz = None
        result = None
        error = None

        if selected_quiz_id:
            quiz_obj = self.contentRepository.getQuizDetails(selected_quiz_id)
            if quiz_obj:
                selected_quiz = quiz_for_template(quiz_obj)
            else:
                error = "Selected quiz could not be found."

        if request.method == "POST" and selected_quiz:
            submitted_answers = {
                question.questionId: request.form.get(question.questionId, "")
                for question in selected_quiz.questions
            }
            result = self.contentRepository.submitQuizResults(
                selected_quiz.quiz_id,
                submitted_answers,
            )

        return render_template(
            "quiz.html",
            quizzes=quizzes,
            selected_quiz=selected_quiz,
            selected_species=selected_species,
            selected_topic=selected_topic,
            should_show_available_quizzes=should_show_available_quizzes,
            supported_species=SUPPORTED_SPECIES,
            quiz_topics=QUIZ_TOPICS,
            result=result,
            error=error,
        )

    def manageAlerts(self):
        guard = require_login()
        if guard:
            return guard

        saved_region = get_current_user_region()
        region = saved_region if get_current_role() == "PetOwner" else ""
        active_alerts = None
        message = None
        mode = request.args.get("mode", "")

        if request.method == "POST":
            action = request.form.get("action")
            session_user = current_session_user()
            mode = "create" if action == "create" else "fetch"

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

                alert_id = self.alertBroadcaster.distributeNewAlert(
                    staffUserId=session_user["userId"],
                    title=title,
                    description=description,
                    region=region,
                    severity=severity,
                )
                message = f"Alert {alert_id} created and saved to database."

            if action == "fetch":
                region = form_text("region") or saved_region

        if region:
            active_alerts = [
                alert_for_template(alert)
                for alert in self.alertBroadcaster.fetchLocalAlerts(region)
            ]

        return render_template(
            "alerts.html",
            region=region,
            saved_region=saved_region,
            mode=mode,
            alerts=active_alerts,
            message=message,
        )

    def submitContent(self):
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

            request_id = self.contentModerator.initiateSubmission(
                vetUserId=session_user["userId"],
                contentType=content_type,
                contentDataPayload=content_data,
            )
            message = f"Submission {request_id} saved to database and is pending review."

        return render_template("submit_content.html", message=message)

    def reviewModerationQueue(self):
        guard = require_role(ROLE_ASSOCIATION_STAFF)
        if guard:
            return guard

        message = None

        if request.method == "POST":
            session_user = current_session_user()
            request_id = form_text("request_id")
            decision = request.form.get("decision", "")
            final_status = STATUS_APPROVED if decision == "approve" else STATUS_REJECTED

            success = self.contentModerator.processReviewDecision(
                requestId=request_id,
                staffUserId=session_user["userId"],
                finalStatus=final_status,
            )

            if success:
                message = f"Request {request_id} marked as {final_status.capitalize()}."

        requests = [
            request_for_template(approval_request)
            for approval_request in self.contentModerator.getPendingQueue()
        ]
        return render_template("moderation.html", requests=requests, message=message)

    def manageVetDetails(self):
        guard = require_role(ROLE_ASSOCIATION_STAFF)
        if guard:
            return guard

        message = None

        if request.method == "POST":
            session_user = current_session_user()
            specialisations = [
                item.strip().lower()
                for item in request.form.get("specialisations", "").split(",")
                if item.strip()
            ]

            clinic_data = {
                "clinicName": form_text("clinic_name"),
                "licenseNumber": form_text("license_number"),
                "specialisations": specialisations,
                "region": form_text("region"),
                "contactInfo": {
                    "phone": form_text("phone"),
                    "address": form_text("address"),
                    "email": form_text("email"),
                    "mapsLink": form_text("maps_link"),
                },
                "operatingHours": form_text("operating_hours"),
                "isActive": True,
            }

            vet_id = self.contentRepository.addVetDetails(
                clinicData=clinic_data,
                staffUserId=session_user["userId"],
            )
            message = f"Vet clinic {vet_id} added and saved to database."

        return render_template("vet_details.html", message=message)
