from types import SimpleNamespace

from app_context import URGENCY_TO_TEMPLATE


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
        phone=contact_info.get("phone", ""),
        address=contact_info.get("address", ""),
        email=contact_info.get("email", ""),
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
        sex=pet.sex,
        is_neutered=pet.isNeutered,
        medical_history=", ".join(pet.medicalHistory),
        emergency_notes=pet.emergencyNotes,
    )


def quiz_for_template(quiz):
    return SimpleNamespace(
        quiz_id=quiz.quizId,
        title=quiz.title,
        topic=quiz.topic,
        species=quiz.species,
        difficulty_level=quiz.difficultyLevel,
        questions=quiz.questions,
        question_count=quiz.questionCount,
    )
