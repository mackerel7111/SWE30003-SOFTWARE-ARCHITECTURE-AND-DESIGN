from flask import redirect, render_template, request, url_for

from app_context import (
    ROLE_ASSOCIATION_STAFF,
    URGENCY_FROM_FORM,
    URGENCY_NON_URGENT,
    app,
    alert_broadcaster,
)
from web.session_helpers import current_session_user, form_text, get_current_role, get_current_user_region, require_login
from web.template_adapters import alert_for_template


@app.route("/alerts", methods=["GET", "POST"])
def alerts():
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

            alert_id = alert_broadcaster.distributeNewAlert(
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
            for alert in alert_broadcaster.fetchLocalAlerts(region)
        ]

    return render_template(
        "alerts.html",
        region=region,
        saved_region=saved_region,
        mode=mode,
        alerts=active_alerts,
        message=message,
    )
