from flask import render_template, request

from app_context import ROLE_ASSOCIATION_STAFF, app, content_repository
from web.session_helpers import current_session_user, form_text, require_role


@app.route("/vet-details", methods=["GET", "POST"])
def vet_details():
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

        vet_id = content_repository.addVetDetails(
            clinicData=clinic_data,
            staffUserId=session_user["userId"],
        )
        message = f"Vet clinic {vet_id} added and saved to database."

    return render_template("vet_details.html", message=message)
