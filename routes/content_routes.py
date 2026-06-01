from flask import render_template, request

from app_context import (
    ROLE_ASSOCIATION_STAFF,
    ROLE_VET_PARTNER,
    STATUS_APPROVED,
    STATUS_REJECTED,
    URGENCY_NON_URGENT,
    app,
    content_moderator,
)
from web.session_helpers import current_session_user, form_text, require_role
from web.template_adapters import request_for_template


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
