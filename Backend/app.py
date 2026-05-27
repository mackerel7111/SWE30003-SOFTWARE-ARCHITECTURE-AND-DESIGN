"""
app.py — Presentation / API Routing Layer (REST API)
Pet First-Aid Web Application

This module serves as the RESTful API backend. It intercepts incoming HTTP 
client requests (JSON payloads), enforces parameter validation, delegates 
business logic to services.py, and returns standardized JSON responses 
for the frontend team to consume.
"""

import logging
from flask import Flask, request, jsonify, session
from Backend.database import Database
from Backend.services import (
    AuthenticationManager, TriageEngine, SearchEngine, 
    ContentRepository, ContentModerator, AlertBroadcaster
)

# Initialize Flask app instance
app = Flask(__name__)
app.secret_key = "PFA_PROTOTYPE_SUPER_SECRET_SESSION_KEY_EGB"

# Setup application logging context
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize single system instances of core control layer services
authManager = AuthenticationManager()
triageEngine = TriageEngine()
searchEngine = SearchEngine()
contentMod = ContentModerator()
alertBroadcaster = AlertBroadcaster()


_databaseSeeded = False

@app.before_request
def seedPrototypeDatabase():
    """
    Ensure the MongoDB collections are seeded with prototype mock data
    exactly once before processing the first application request.
    """
    global _databaseSeeded
    if not _databaseSeeded:
        try:
            db = Database()
            db.seed_data()
            _databaseSeeded = True
        except Exception as err:
            logger.error("Failed to run automatic database setup seeding: %s", str(err))

# ===========================================================================
# 1. API: DASHBOARD & AUTHENTICATION
# ===========================================================================

@app.route("/api/dashboard", methods=["GET"])
def getDashboardInfo():
    """Returns general dashboard data like active regional alerts."""
    try:
        region = request.args.get("region", "Kuala Lumpur")
        activeAlerts = alertBroadcaster.fetchLocalAlerts(region)
        return jsonify({
            "status": "success",
            "region": region,
            "alerts": [alert.toDict() for alert in activeAlerts]
        }), 200
    except Exception as err:
        logger.exception("Error fetching dashboard data: %s", str(err))
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    """Authenticates a user and establishes a session."""
    try:
        data = request.get_json()
        if not data or not data.get("email") or not data.get("password"):
            return jsonify({"status": "error", "message": "Email and password required."}), 400

        sessionData = authManager.authenticateUser(data["email"], data["password"])
        if sessionData:
            session["user"] = sessionData
            return jsonify({
                "status": "success", 
                "message": f"Welcome {sessionData['fullName']}",
                "user": sessionData
            }), 200
        else:
            return jsonify({"status": "error", "message": "Invalid credentials."}), 401

    except Exception as err:
        logger.error("Login sequence exception: %s", str(err))
        return jsonify({"status": "error", "message": "Authentication failed."}), 500


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    """Clears the active session."""
    session.clear()
    return jsonify({"status": "success", "message": "Logged out successfully."}), 200


# ===========================================================================
# 2. API: PET TRIAGE ENGINE
# ===========================================================================

@app.route("/api/triage/evaluate", methods=["POST"])
def evaluateTriage():
    """
    Evaluates pet symptoms and returns urgency level and recommended guides.
    Expected JSON: {"species": "dog", "symptoms": ["choking", "panting"]}
    """
    if not session.get("user"):
        return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401

    try:
        data = request.get_json()
        species = data.get("species", "").strip()
        symptoms = data.get("symptoms", [])

        if not species:
            return jsonify({"status": "error", "message": "Species is required."}), 400

        # Run business logic
        assessmentResult = triageEngine.evaluateSymptoms(species, symptoms)
        
        # Fetch relevant first-aid guides
        relevantGuides = []
        for symptom in symptoms:
            matchedGuides = searchEngine.queryFirstAidGuides(species, symptom)
            relevantGuides.extend([g.toDict() for g in matchedGuides])

        return jsonify({
            "status": "success",
            "assessment": assessmentResult,
            "recommendedGuides": relevantGuides
        }), 200

    except ValueError as valErr:
        return jsonify({"status": "error", "message": str(valErr)}), 400
    except Exception as err:
        logger.exception("Triage API error: %s", str(err))
        return jsonify({"status": "error", "message": "Failed to analyze symptoms."}), 500


# ===========================================================================
# 3. API: CONTENT MODERATION
# ===========================================================================

@app.route("/api/moderation/queue", methods=["GET"])
def getPendingQueue():
    """Returns a list of unreviewed content for Association Staff."""
    sessionUser = session.get("user")
    if not authManager.verifyRole(sessionUser, ["association_staff"]):
        return jsonify({"status": "error", "message": "Forbidden. Staff clearance required."}), 403

    try:
        pendingRequests = contentMod.getPendingQueue()
        return jsonify({
            "status": "success",
            "pendingRequests": [req.toDict() for req in pendingRequests]
        }), 200
    except Exception as err:
        logger.exception("Queue error: %s", str(err))
        return jsonify({"status": "error", "message": "Failed to fetch queue."}), 500


@app.route("/api/moderation/review/<requestId>", methods=["POST"])
def reviewSubmission(requestId):
    """Processes approval or rejection of content."""
    sessionUser = session.get("user")
    if not authManager.verifyRole(sessionUser, ["association_staff"]):
        return jsonify({"status": "error", "message": "Forbidden. Staff clearance required."}), 403

    try:
        data = request.get_json()
        actionDecision = data.get("actionDecision", "").strip() # "approved" or "rejected"
        notes = data.get("reviewNotes", "").strip()

        success = contentMod.processReviewDecision(
            requestId=requestId,
            staffUserId=sessionUser["userId"],
            finalStatus=actionDecision,
            notes=notes
        )

        if success:
            return jsonify({"status": "success", "message": f"Item marked as {actionDecision}."}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to update status."}), 400

    except Exception as err:
        logger.exception("Review error: %s", str(err))
        return jsonify({"status": "error", "message": "Moderation failure."}), 500
    
    
@app.route("/api/vets", methods=["POST"])
def createVetDetails():
    sessionUser = session.get("user")

    if not authManager.verifyRole(sessionUser, ["association_staff"]):
        return jsonify({"status": "error", "message": "Forbidden. Staff access required."}), 403

    data = request.get_json()

    try:
        repository = ContentRepository()
        vetId = repository.addVetDetails(data, sessionUser["userId"])

        return jsonify({
            "status": "success",
            "message": "Vet details added successfully.",
            "vetDetailsId": vetId
        }), 201

    except Exception as err:
        return jsonify({
            "status": "error",
            "message": str(err)
        }), 400
        
if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)