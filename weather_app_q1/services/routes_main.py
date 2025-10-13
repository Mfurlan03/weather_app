# Imports
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from models import db, Location, WeatherSnapshot
from schemas import SearchQuery
from services.geocoding import coordinates_from_query, reverse_geocode
from services.weather import fetch_weather, WMO
from insights import insights_from_payload

bp = Blueprint("main", __name__)

# Home page
@bp.route('/', methods=['GET'])
def index():
    # Show all saved locations when the app loads
    locations = Location.query.order_by(Location.created_at.desc()).all()
    return render_template("index.html", locations=locations)


# Search by user input
@bp.route('/search', methods=['POST'])
def search():
    # Validate whatever the user typed (city, zip, coords, etc.)
    try:
        model = SearchQuery(q=request.form.get('q', ''))
    except Exception as e:
        return render_template("index.html", error=str(e), locations=Location.query.all())

    # Convert the user input into coordinates
    coords = coordinates_from_query(model.q)
    if not coords:
        return render_template("index.html",
                               error="Could not find that place. Try a city, landmark, postal code, or lat,lon.",
                               locations=Location.query.all())

    lat, lon, display = coords

    # Call the weather API for this spot
    try:
        payload = fetch_weather(lat, lon)
    except Exception as e:
        return render_template("index.html", error=f"Weather lookup failed: {e}", locations=Location.query.all())

    # Save the API response so I can “prove” I really fetched data
    snap = WeatherSnapshot(payload_json=json.dumps(payload),
                           location=Location(name=display, latitude=lat, longitude=lon))
    db.session.add(snap.location)
    db.session.add(snap)
    db.session.commit()

    # Translate weather codes into something interpretable and add tips
    wmo = WMO.get(payload.get('current', {}).get('weather_code'), '—')
    wmo_daily = [WMO.get(code, '—') for code in payload.get('daily', {}).get('weather_code', [])]
    tips = insights_from_payload(payload)

    # Render results on the homepage
    return render_template("index.html",
                           weather=payload,
                           place=display,
                           wmo=wmo,
                           wmo_daily=wmo_daily,
                           when=datetime.now().strftime('%Y-%m-%d %H:%M'),
                           tips=tips,
                           locations=Location.query.order_by(Location.created_at.desc()).all())


# Use browser's GPS 
@bp.route('/use-my-location', methods=['POST'])
def use_my_location():
    # Grab GPS coords from the browser 
    try:
        lat = float(request.form.get('lat'))
        lon = float(request.form.get('lon'))
    except Exception:
        return jsonify({"error": "Bad coordinates."}), 400

    # Takes the latitude/longitude numbers and translate them into a readable location name for display (like Toronto, ON)
    name = reverse_geocode(lat, lon) or f"{lat:.3f}, {lon:.3f}"
    return jsonify({"redirect": url_for('main.search_coords', lat=lat, lon=lon, name=name)})


# Search by coords 
@bp.route('/search/coords')
def search_coords():
    # Handles lat/lon searches (used by GPS feature)
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    display = request.args.get('name') or f"{lat:.3f}, {lon:.3f}"

    try:
        payload = fetch_weather(lat, lon)
    except Exception as e:
        return render_template("index.html", error=f"Weather lookup failed: {e}", locations=Location.query.all())

    snap = WeatherSnapshot(payload_json=json.dumps(payload),
                           location=Location(name=display, latitude=lat, longitude=lon))
    db.session.add(snap.location)
    db.session.add(snap)
    db.session.commit()

    wmo = WMO.get(payload.get('current', {}).get('weather_code'), '—')
    wmo_daily = [WMO.get(code, '—') for code in payload.get('daily', {}).get('weather_code', [])]
    tips = insights_from_payload(payload)

    return render_template("index.html",
                           weather=payload,
                           place=display,
                           wmo=wmo,
                           wmo_daily=wmo_daily,
                           when=datetime.now().strftime('%Y-%m-%d %H:%M'),
                           tips=tips,
                           locations=Location.query.order_by(Location.created_at.desc()).all())


# CRUD: saved locations
@bp.route('/locations', methods=['POST'])
def create_location():
    # Let users save a location with a particular name
    name = (request.form.get('name') or '').strip()
    q = (request.form.get('q') or '').strip()
    if not name or not q:
        return redirect(url_for('main.index'))

    coords = coordinates_from_query(q)
    if not coords:
        return render_template("index.html", error="Could not find that place.", locations=Location.query.all())

    lat, lon, _ = coords
    loc = Location(name=name, latitude=lat, longitude=lon)
    db.session.add(loc)
    db.session.commit()
    return redirect(url_for('main.index'))


@bp.route('/locations/<int:loc_id>/update', methods=['POST'])
def update_location(loc_id):
    # Allows for renaming saved locations
    loc = Location.query.get_or_404(loc_id)
    name = (request.form.get('name') or '').strip()
    if name:
        loc.name = name
        db.session.commit()
    return redirect(url_for('main.index'))


@bp.route('/locations/<int:loc_id>/delete', methods=['POST'])
def delete_location(loc_id):
    # Remove a location and its associated snapshots
    loc = Location.query.get_or_404(loc_id)
    db.session.delete(loc)
    db.session.commit()
    return redirect(url_for('main.index'))


@bp.route('/locations/<int:loc_id>/weather')
def view_location_weather(loc_id):
    # Re-gathers the weather for a location the user already saved
    loc = Location.query.get_or_404(loc_id)
    try:
        payload = fetch_weather(loc.latitude, loc.longitude)
    except Exception as e:
        return render_template("index.html", error=f"Weather lookup failed: {e}", locations=Location.query.all())

    snap = WeatherSnapshot(payload_json=json.dumps(payload), location=loc)
    db.session.add(snap)
    db.session.commit()

    wmo = WMO.get(payload.get('current', {}).get('weather_code'), '—')
    wmo_daily = [WMO.get(code, '—') for code in payload.get('daily', {}).get('weather_code', [])]
    tips = insights_from_payload(payload)

    return render_template("index.html",
                           weather=payload,
                           place=loc.name,
                           wmo=wmo,
                           wmo_daily=wmo_daily,
                           when=datetime.now().strftime('%Y-%m-%d %H:%M'),
                           tips=tips,
                           locations=Location.query.order_by(Location.created_at.desc()).all())
