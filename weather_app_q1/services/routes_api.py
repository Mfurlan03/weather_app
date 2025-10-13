from flask import Blueprint, request, jsonify
from models import db, Location
from services.geocoding import coordinates_from_query
from services.weather import fetch_weather

# This blueprint handles API routes (separate from the UI in routes_main.py)
bp = Blueprint("api", __name__)


# Weather lookup via API 
@bp.route('/api/weather')
def api_weather():
    # Takes in a query (city name, landmark, or lat/lon) and return live weather as JSON
    coords = coordinates_from_query(request.args.get('q'))
    if not coords:
        return jsonify({"error": "not_found"}), 404
    lat, lon, display = coords
    payload = fetch_weather(lat, lon)
    return jsonify({"place": display, "data": payload})


# Get all saved locations 
@bp.route('/api/locations', methods=['GET'])
def api_locations_list():
    # Return every saved location from the DB as JSON
    locs = Location.query.order_by(Location.created_at.desc()).all()
    return jsonify([{"id": l.id, "name": l.name, "lat": l.latitude, "lon": l.longitude} for l in locs])


# Create a new location 
@bp.route('/api/locations', methods=['POST'])
def api_locations_create():
    # Accept JSON body with name and query to save a location
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get('name') or '').strip()
    q = (body.get('q') or '').strip()
    if not name or not q:
        return jsonify({"error": "bad_request"}), 400

    # Validate and geocode input
    coords = coordinates_from_query(q)
    if not coords:
        return jsonify({"error": "not_found"}), 404

    # Save new location in DB
    lat, lon, _ = coords
    loc = Location(name=name, latitude=lat, longitude=lon)
    db.session.add(loc)
    db.session.commit()
    return jsonify({"id": loc.id}), 201


# Update a location
@bp.route('/api/locations/<int:loc_id>', methods=['PATCH'])
def api_locations_update(loc_id):
    # Update location fields ( only name is editable)
    loc = Location.query.get_or_404(loc_id)
    body = request.get_json(force=True, silent=True) or {}
    if 'name' in body:
        name = (body['name'] or '').strip()
        if name:
            loc.name = name
    db.session.commit()
    return jsonify({"ok": True})


#  Delete a location
@bp.route('/api/locations/<int:loc_id>', methods=['DELETE'])
def api_locations_delete(loc_id):
    # Delete location and remove any weather snapshots tied to it
    loc = Location.query.get_or_404(loc_id)
    db.session.delete(loc)
    db.session.commit()
    return jsonify({"ok": True})
