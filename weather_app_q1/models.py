
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import func

db = SQLAlchemy()

class Location(db.Model):

    # Defines the database tables for Locations
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)  
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # the timestamps that are created here are used because you can see when data was created/changed.
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # Link locations to their weather snapshots and auto-delete snapshots if the location is removed
    snapshots = relationship("WeatherSnapshot", back_populates="location", cascade="all, delete-orphan")

class WeatherSnapshot(db.Model):

    # Defines the database tables for Weather Snapshots
    __tablename__ = 'weather_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    fetched_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    # Store the JSON payload returned by the weather API
    payload_json = db.Column(db.Text, nullable=False)

    # Lets each snapshot easily access the Location it belongs to
    location = relationship("Location", back_populates="snapshots")
