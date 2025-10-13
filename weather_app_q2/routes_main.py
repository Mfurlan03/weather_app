# Imports
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from models import db, Location, WeatherSnapshot, WeatherRequest
from schemas import SearchQuery, RangeRequest
from geocoding import coordinates_from_query, reverse_geocode
from weather import fetch_weather, fetch_weather_range, WMO
from insights import insights_from_payload
from pydantic import ValidationError

bp = Blueprint("main", __name__)

# Creates an error message from Pydantic validation errors
def friendly_pydantic_error(err: Exception) -> str:
    if isinstance(err, ValidationError):
        return "; ".join(e.get("msg", "Invalid input") for e in err.errors())
    return str(err)

# Renders the home page
@bp.route('/', methods=['GET'])
def index():
    locations = Location.query.order_by(Location.created_at.desc()).all()
    requests_list = WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all()
    return render_template("index.html", locations=locations, requests_list=requests_list)

# Handles search form submissions
@bp.route('/search', methods=['POST'])
def search():
    try:
        model = SearchQuery(q=request.form.get('q', ''))
    except Exception as e:
        return render_template("index.html", error=str(e), locations=Location.query.all())

    coords = coordinates_from_query(model.q)
    if not coords:
        return render_template("index.html",
                               error="Could not find that place. Try a city, landmark, postal code, or lat,lon.",
                               locations=Location.query.all())

    lat, lon, display = coords

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
                           locations=Location.query.order_by(Location.created_at.desc()).all(),
                           requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all(),
                           maps_lat=lat, maps_lon=lon)

# Handles location lookup from browser’s GPS
@bp.route('/use-my-location', methods=['POST'])
def use_my_location():
    try:
        lat = float(request.form.get('lat'))
        lon = float(request.form.get('lon'))
    except Exception:
        return jsonify({"error": "Bad coordinates."}), 400

    name = reverse_geocode(lat, lon) or f"{lat:.3f}, {lon:.3f}"
    return jsonify({"redirect": url_for('main.search_coords', lat=lat, lon=lon, name=name)})

# Handles searches from lat/lon query parameters
@bp.route('/search/coords')
def search_coords():
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
                           locations=Location.query.order_by(Location.created_at.desc()).all(),
                           requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all(),
                           maps_lat=lat, maps_lon=lon)

# Creates a new historical weather request
@bp.route('/requests', methods=['POST'])
def create_request():
    try:
        model = RangeRequest(
            name=request.form.get('name',''),
            q=request.form.get('q',''),
            start_date=request.form.get('start_date',''),
            end_date=request.form.get('end_date',''),
            allow_fuzzy=request.form.get('fuzzy') == 'on'
        )
    except Exception as e:
        return render_template(
            "index.html",
            error=friendly_pydantic_error(e),
            locations=Location.query.all(),
            requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all()
        )

    coords = coordinates_from_query(model.q, allow_fuzzy=model.allow_fuzzy)
    if not coords:
        return render_template("index.html", error="Could not find that place.",
                               locations=Location.query.all(),
                               requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all())
    lat, lon, display = coords
    try:
        payload = fetch_weather_range(lat, lon, model.start_date, model.end_date)
    except Exception as e:
        return render_template("index.html", error=f"Historical lookup failed: {e}",
                               locations=Location.query.all(),
                               requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all())

    wr = WeatherRequest(
        name=model.name,
        display_name=display,
        latitude=lat,
        longitude=lon,
        start_date=model.start_date,
        end_date=model.end_date,
        payload_json=json.dumps(payload)
    )
    db.session.add(wr)
    db.session.commit()
    return redirect(url_for('main.index'))

# Updates an existing historical request
@bp.route('/requests/<int:req_id>/update', methods=['POST'])
def update_request(req_id):
    wr = WeatherRequest.query.get_or_404(req_id)
    start = request.form.get('start_date') or wr.start_date.isoformat()
    end = request.form.get('end_date') or wr.end_date.isoformat()
    new_name = (request.form.get('name') or wr.name).strip()

    try:
        model = RangeRequest(
            name=new_name,
            q=f"{wr.latitude},{wr.longitude}",
            start_date=start,
            end_date=end,
            allow_fuzzy=True
        )
    except Exception as e:
        return render_template(
            "index.html",
            error=friendly_pydantic_error(e),
            locations=Location.query.all(),
            requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all()
        )

    wr.name = model.name
    wr.start_date = model.start_date
    wr.end_date = model.end_date

    try:
        payload = fetch_weather_range(wr.latitude, wr.longitude, wr.start_date, wr.end_date)
        wr.payload_json = json.dumps(payload)
    except Exception as e:
        return render_template("index.html", error=f"Refetch failed: {e}",
                               locations=Location.query.all(),
                               requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all())
    db.session.commit()
    return redirect(url_for('main.index'))

# Deletes a historical weather request
@bp.route('/requests/<int:req_id>/delete', methods=['POST'])
def delete_request(req_id):
    wr = WeatherRequest.query.get_or_404(req_id)
    db.session.delete(wr)
    db.session.commit()
    return redirect(url_for('main.index'))

# Creates a new saved location
@bp.route('/locations', methods=['POST'])
def create_location():
    name = (request.form.get('name') or '').strip()
    q = (request.form.get('q') or '').strip()
    if not name or not q:
        return redirect(url_for('main.index'))

    coords = coordinates_from_query(q)
    if not coords:
        return render_template(
            "index.html",
            error="Could not find that place.",
            locations=Location.query.all(),
            requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all()
        )

    lat, lon, _ = coords
    loc = Location(name=name, latitude=lat, longitude=lon)
    db.session.add(loc)
    db.session.commit()
    return redirect(url_for('main.index'))

# Updates a saved location’s name
@bp.route('/locations/<int:loc_id>/update', methods=['POST'])
def update_location(loc_id):
    loc = Location.query.get_or_404(loc_id)
    name = (request.form.get('name') or '').strip()
    if name:
        loc.name = name
        db.session.commit()
    return redirect(url_for('main.index'))

# Deletes a saved location
@bp.route('/locations/<int:loc_id>/delete', methods=['POST'])
def delete_location(loc_id):
    loc = Location.query.get_or_404(loc_id)
    db.session.delete(loc)
    db.session.commit()
    return redirect(url_for('main.index'))

# Fetches and displays current weather for a saved location
@bp.route('/locations/<int:loc_id>/weather')
def view_location_weather(loc_id):
    loc = Location.query.get_or_404(loc_id)
    try:
        payload = fetch_weather(loc.latitude, loc.longitude)
    except Exception as e:
        return render_template(
            "index.html",
            error=f"Weather lookup failed: {e}",
            locations=Location.query.all(),
            requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all()
        )

    snap = WeatherSnapshot(payload_json=json.dumps(payload), location=loc)
    db.session.add(snap)
    db.session.commit()

    wmo = WMO.get(payload.get('current', {}).get('weather_code'), '—')
    wmo_daily = [WMO.get(code, '—') for code in payload.get('daily', {}).get('weather_code', [])]
    tips = insights_from_payload(payload)

    return render_template(
        "index.html",
        weather=payload,
        place=loc.name,
        wmo=wmo,
        wmo_daily=wmo_daily,
        when=datetime.now().strftime('%Y-%m-%d %H:%M'),
        tips=tips,
        locations=Location.query.order_by(Location.created_at.desc()).all(),
        requests_list=WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all(),
        maps_lat=loc.latitude,
        maps_lon=loc.longitude
    )
