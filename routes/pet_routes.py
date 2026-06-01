from flask import render_template, request

from app_context import ROLE_PET_OWNER, PetProfile, app, database
from web.session_helpers import current_session_user, form_text, require_role
from web.template_adapters import pet_for_template


@app.route("/pets", methods=["GET", "POST"])
def pets():
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
                existing_pet = database.findPetById(pet_id)
                if not existing_pet or existing_pet.get("ownerId") != session_user["userId"]:
                    raise ValueError("Please select a valid pet profile to edit.")

                database.updatePetProfile(pet_id, pet_data)
                message = "Pet profile updated."
            else:
                pet_profile = PetProfile(
                    ownerId=session_user["userId"],
                    **pet_data,
                )
                pet_id = database.insertPetProfile(pet_profile.toDict())
                message = f"Pet profile {pet_id} saved."
        except ValueError as err:
            error = str(err)
            form_mode = request.form.get("action", form_mode)
            selected_pet_id = request.form.get("pet_id", selected_pet_id)

    pet_documents = database.findPetsByOwner(session_user["userId"])
    saved_pets = [pet_for_template(PetProfile.fromDict(pet)) for pet in pet_documents]

    if form_mode == "edit" and selected_pet_id:
        pet_document = database.findPetById(selected_pet_id)
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
