from flask import render_template, request

from app_context import (
    ROLE_PET_OWNER,
    SUPPORTED_SPECIES,
    app,
    content_repository,
    search_engine,
)
from web.session_helpers import form_text, get_current_user_region, require_role
from web.template_adapters import clinic_for_template, guide_for_template, video_for_template


@app.route("/search", methods=["GET", "POST"])
def search():
    guard = require_role(ROLE_PET_OWNER)
    if guard:
        return guard

    keyword = ""
    search_type = "guide"
    guides = None
    clinics = None
    videos = None
    saved_region = get_current_user_region()
    selected_species = "dog"

    if request.method == "GET":
        keyword = request.args.get("keyword", "").strip()
        search_type = request.args.get("search_type", search_type)
        selected_species = request.args.get("species", selected_species)

    if request.method == "POST" or request.args.get("auto") == "1":
        if request.method == "POST":
            keyword = form_text("keyword")
            search_type = request.form.get("search_type", "guide")
            selected_species = request.form.get("species", selected_species)

        if search_type == "guide":
            matched_guides = search_engine.queryFirstAidGuides(selected_species.lower(), keyword)
            guides = [guide_for_template(guide) for guide in matched_guides]

        if search_type == "clinic":
            keyword = keyword or saved_region
            clinics = [
                clinic_for_template(clinic)
                for clinic in search_engine.searchVetsByRegion(keyword)
            ]

        if search_type == "video":
            keyword = selected_species
            videos = [
                video_for_template(video)
                for video in content_repository.getApprovedVideos(selected_species.lower())
            ]

    return render_template(
        "search.html",
        keyword=keyword,
        search_type=search_type,
        guides=guides,
        clinics=clinics,
        videos=videos,
        saved_region=saved_region,
        selected_species=selected_species,
        supported_species=SUPPORTED_SPECIES,
    )
