from app_context import app, database
from routes import register_routes


database.seed_data()
register_routes()


if __name__ == "__main__":
    app.run(debug=True)
