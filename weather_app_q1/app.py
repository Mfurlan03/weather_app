# Imports
import os
from flask import Flask
from models import db
from services.routes_main import bp as main_blueprint
from services.routes_api import bp as api_blueprint

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Ensure instance/ exists 
    os.makedirs(app.instance_path, exist_ok=True)

    # Database configuration
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        db_url = "sqlite:///" + os.path.join(app.instance_path, "weather.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint)
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
