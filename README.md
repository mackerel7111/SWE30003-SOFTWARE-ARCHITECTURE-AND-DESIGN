PetFirstAid

PetFirstAid is a Flask-based web prototype developed for the SWE30003 Software Architecture and Design Assignment 3.
The system implements an object-oriented Boundary–Control–Entity (BCE) architecture and demonstrates a fully functional web application using MongoDB for persistent storage.

------------------------------------------------------------
TECH STACK
------------------------------------------------------------
- Python 3.8+
- Flask (web framework)
- Jinja2 (HTML templating)
- Bootstrap (via CDN)
- MongoDB (local database)
- pip (dependency management)

------------------------------------------------------------
PROJECT STRUCTURE
------------------------------------------------------------
PetFirstAid/
  main.py                      Flask application entry point
  app_context.py               Application initialization
  app_routing.py               Flask route configuration
  pyproject.toml               Project dependencies and metadata
  Backend/
    database.py                Boundary layer (MongoDB interface)
    requirements.txt           Python dependencies
    models/                    Entity layer (domain objects)
      user.py
      pet_owner.py
      veterinary_partner.py
      association_staff.py
      pet_profile.py
      first_aid_guide.py
      instructional_video.py
      educational_quiz.py
      quiz_question.py
      quiz_feedback.py
      approval_request.py
      regional_alert.py
      vet_details.py
      common.py
    services/                  Control layer (business logic)
      authentication_manager.py
      content_moderator.py
      content_repository.py
      search_engine.py
      triage_engine.py
      alert_broadcaster.py
  web/                         Session and template helper utilities
    session_helpers.py
    template_adapters.py
  routes/                      Route handlers
  templates/                   HTML templates (UI layer)
    base.html
    login.html
    register.html
    dashboard.html
    pets.html
    quiz.html
    search.html
    alerts.html
    triage.html
    vet_details.html
    moderation.html
    submit_content.html
  static/                      CSS and static files
    style.css

------------------------------------------------------------
SYSTEM OVERVIEW
------------------------------------------------------------
PetFirstAid is a role-based veterinary assistance system for:

- Pet Owners
- Association Staff
- Veterinary Partners

The system supports:
- Pet symptom triage and urgency evaluation
- First-aid guidance and vet recommendations
- Veterinary content submission and moderation
- Regional alerts broadcast and retrieval
- Pet profile management
- Educational quizzes

All data is stored in MongoDB and automatically seeded with demo data on first run.

------------------------------------------------------------
SETUP INSTRUCTIONS
------------------------------------------------------------

1. Navigate to project directory:
cd PetFirstAid

2. Install dependencies:
python -m pip install -r Backend\requirements.txt

3. Start MongoDB:
net start MongoDB

4. Optional: Check for syntax errors:
python -m compileall Backend app_routing.py app_context.py main.py web

------------------------------------------------------------
RUN APPLICATION
------------------------------------------------------------

Standard run:
python main.py

Using uv (optional):
uv run python main.py

------------------------------------------------------------
ACCESS APPLICATION
------------------------------------------------------------
http://127.0.0.1:5000

------------------------------------------------------------
DEMO ACCOUNTS
------------------------------------------------------------

Pet Owner:
owner@example.com / ownerpass

Association Staff:
staff@example.com / staffpass

Veterinary Partner:
vet@example.com / vetpass

------------------------------------------------------------
IMPLEMENTED FEATURES
------------------------------------------------------------
- User login and role-based dashboard
- Pet symptom triage with urgency output
- First-aid guidance and vet suggestions
- Veterinary clinic search with Google Maps integration
- Regional alerts system (create and fetch alerts)
- Veterinary content submission and moderation workflow
- Pet profile management (add/edit/view)
- Educational quizzes

------------------------------------------------------------
SYSTEM BEHAVIOR
------------------------------------------------------------
- Flask handles routing and session control
- MongoDB stores all persistent data
- BCE architecture separates:
  - Entities (data models)
  - Controls (business logic)
  - Boundaries (database access)
- Demo data is automatically seeded on first execution

------------------------------------------------------------
LOGOUT & ACCESS CONTROL
------------------------------------------------------------
- /logout clears the user session
- Users are redirected to login page
- Ensures secure role-based access control

------------------------------------------------------------
NOTES
------------------------------------------------------------
This is an academic prototype developed for software architecture evaluation.
It demonstrates full-stack integration using Flask, MongoDB, and object-oriented BCE design principles.