from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import func

db = SQLAlchemy()

# Represents a saved location with name and coordinates
class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    snapshots = relationship("WeatherSnapshot", back_populates="location", cascade="all, delete-orphan")

# Represents a stored weather snapshot for a specific location
class WeatherSnapshot(db.Model):
    __tablename__ = 'weather_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    fetched_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    payload_json = db.Column(db.Text, nullable=False)
    location = relationship("Location", back_populates="snapshots")

# Stores historical weather requests and their results
class WeatherRequest(db.Model):
    __tablename__ = 'weather_requests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    display_name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    payload_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
