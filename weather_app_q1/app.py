# This file creates and runs the Weather App.

# Imports
from flask import Flask
from models import db
from services.routes_main import bp as main_blueprint
from services.routes_api import bp as api_blueprint

def create_app():

    # Make a new Flask app
    app = Flask(__name__)

    # Calls the weather database from weather.db every time the app is ran
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Links the database to this app
    db.init_app(app)

    # Creates the tables if they don't exist yet
    with app.app_context():
        db.create_all()

    # Add routes from routes_main.py
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint)
    return app


# Runs the server 
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)  
