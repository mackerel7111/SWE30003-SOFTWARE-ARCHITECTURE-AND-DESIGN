from flask import redirect, render_template, url_for

from app_context import app
from web.session_helpers import get_current_role, get_current_user, require_login


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

@app.route("/dashboard")
def dashboard():
    guard = require_login()
    if guard:
        return guard
    return render_template("dashboard.html")
