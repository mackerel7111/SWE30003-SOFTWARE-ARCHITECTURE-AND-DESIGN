from flask import render_template, request

from app_context import ROLE_PET_OWNER, QUIZ_TOPICS, SUPPORTED_SPECIES, app, content_repository
from web.session_helpers import require_role
from web.template_adapters import quiz_for_template


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    guard = require_role(ROLE_PET_OWNER)
    if guard:
        return guard

    selected_species = request.values.get("species", "dog")
    selected_topic = request.values.get("topic", "breathing")
    selected_quiz_id = request.form.get("quiz_id") or request.args.get("quiz_id")
    should_show_available_quizzes = (
        request.method == "POST"
        or "species" in request.args
        or "topic" in request.args
        or bool(selected_quiz_id)
    )
    quizzes = []
    if should_show_available_quizzes:
        quizzes = [
            quiz_for_template(quiz)
            for quiz in content_repository.getAllQuizzes()
            if quiz.species == selected_species and quiz.topic == selected_topic
        ]
    selected_quiz = None
    result = None
    error = None

    if selected_quiz_id:
        quiz_obj = content_repository.getQuizDetails(selected_quiz_id)
        if quiz_obj:
            selected_quiz = quiz_for_template(quiz_obj)
        else:
            error = "Selected quiz could not be found."

    if request.method == "POST" and selected_quiz:
        submitted_answers = {
            question.questionId: request.form.get(question.questionId, "")
            for question in selected_quiz.questions
        }
        result = content_repository.submitQuizResults(
            selected_quiz.quiz_id,
            submitted_answers,
        )

    return render_template(
        "quiz.html",
        quizzes=quizzes,
        selected_quiz=selected_quiz,
        selected_species=selected_species,
        selected_topic=selected_topic,
        should_show_available_quizzes=should_show_available_quizzes,
        supported_species=SUPPORTED_SPECIES,
        quiz_topics=QUIZ_TOPICS,
        result=result,
        error=error,
    )
