from flask import Flask
from models import db
from routes_main import bp as main_blueprint
from routes_api import bp as api_blueprint

# Sets up and configures the Flask application
def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint)
    return app

# Runs the app
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
