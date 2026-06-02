from app_context import (
    alert_broadcaster,
    app,
    authentication_manager,
    content_moderator,
    content_repository,
    database,
    search_engine,
    triage_engine,
)
from app_routing import AppRouting


database.seed_data()
app_routing = AppRouting(
    app=app,
    database=database,
    authenticationManager=authentication_manager,
    searchEngine=search_engine,
    triageEngine=triage_engine,
    alertBroadcaster=alert_broadcaster,
    contentModerator=content_moderator,
    contentRepository=content_repository,
)
app_routing.registerRoutes()


if __name__ == "__main__":
    app.run(debug=True)
