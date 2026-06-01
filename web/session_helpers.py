from types import SimpleNamespace

from flask import redirect, request, session, url_for

from app_context import ROLE_LABELS, database


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


def get_current_user_region():
    session_user = current_session_user()
    if not session_user:
        return ""

    user_document = database.findUserById(session_user.get("userId"))
    if not user_document:
        return ""

    return user_document.get("region", "")


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
