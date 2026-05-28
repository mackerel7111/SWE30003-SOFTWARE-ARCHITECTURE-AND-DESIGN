# PetFirstAid

PetFirstAid is a simple Flask web prototype for the SWE30003 Software Architecture and Design Assignment 3 implementation. The backend follows the object-oriented Boundary-Control-Entity structure from the Assignment 2 design.

## Tech Stack

- Python
- Flask
- Jinja2 HTML templates
- Bootstrap via CDN
- MongoDB through the backend Database wrapper
- uv or pip for dependency and environment management

## Project Structure

```text
PetFirstAid/
  main.py              Flask application entry point
  Backend/
    models.py          Entity/domain classes
    services.py        Control/service classes
    database.py        MongoDB persistence boundary
  templates/           HTML templates rendered by Flask/Jinja2
  static/              CSS/static assets
  pyproject.toml       Project dependencies
  uv.lock              Locked dependency versions
```

## Setup

From the project folder:

```powershell
uv sync
```

If `uv` is not available, install Flask in your active Python environment:

```powershell
pip install -r Backend\requirements.txt
```

Make sure MongoDB is installed and running locally before starting the app.

## Run

With the project virtual environment active:

```powershell
python main.py
```

Or with uv:

```powershell
uv run python main.py
```

Open the app at:

```text
http://127.0.0.1:5000/login
```

## Demo Accounts

```text
Pet Owner:
owner@example.com / ownerpass

Association Staff:
staff@example.com / staffpass

Veterinary Partner:
vet@example.com / vetpass
```

## Implemented Demo Flows

- Login and role-aware dashboard
- Pet symptom triage with urgency result
- First-aid guide and clinic search
- Regional alert creation and lookup
- Veterinary partner content submission
- Staff moderation approval/rejection
- Staff-maintained vet clinic directory records
- Educational quizzes

## Notes

This is an assignment prototype. Data is persisted in a local MongoDB database through the `Backend/database.py` wrapper. Flask routes in `main.py` act as the AppRouting/boundary layer that connects the HTML templates to the object-oriented backend classes.
