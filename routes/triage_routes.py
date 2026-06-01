from types import SimpleNamespace

from flask import render_template, request, url_for

from app_context import (
    ROLE_PET_OWNER,
    URGENCY_TO_TEMPLATE,
    URGENCY_URGENT,
    URGENCY_EMERGENCY,
    PetProfile,
    app,
    database,
    search_engine,
    triage_engine,
)
from web.session_helpers import current_session_user, form_text, get_current_user_region, require_role
from web.template_adapters import guide_for_template, pet_for_template


@app.route("/triage", methods=["GET", "POST"])
def triage():
    guard = require_role(ROLE_PET_OWNER)
    if guard:
        return guard

    result = None
    error = None
    session_user = current_session_user()
    saved_region = get_current_user_region()
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
