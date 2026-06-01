from flask import redirect, render_template, request, session, url_for

from app_context import (
    DEMO_LOGIN_ALIASES,
    ROLE_PET_OWNER,
    ROLE_VET_PARTNER,
    PetOwner,
    VeterinaryPartner,
    app,
    authentication_manager,
    database,
)
from web.session_helpers import form_text, get_current_user


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    message = request.args.get("message")

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

    return render_template("login.html", error=error, message=message)


@app.route("/register", methods=["GET", "POST"])
def register():
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

            if database.findUserByEmail(email):
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

            database.insertUser(user.toDict())
            return redirect(url_for("login", message="Registration successful. Please log in."))
        except ValueError as err:
            error = str(err)

    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
