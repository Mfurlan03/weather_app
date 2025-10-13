from flask import Blueprint, request, jsonify, Response
from models import db, Location, WeatherRequest
from geocoding import coordinates_from_query
from weather import fetch_weather, fetch_weather_range, WMO
from schemas import RangeRequest
import json, csv, io
import re

bp = Blueprint("api", __name__)

# Implemented to remove emojis (had issues removing emojis from the daily excel file)
_emoji_re = re.compile(
    "["                     
    "\u2600-\u26FF"         
    "\u2700-\u27BF"         
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\U0001FB00-\U0001FBFF"
    "\uFE0E-\uFE0F"         
    "\u200D"                
    "]+",
    flags=re.UNICODE
)

# Removes emoji and similar symbols from text
def strip_emojis(text: str) -> str:
    if not isinstance(text, str):
        return text
    return _emoji_re.sub("", text).strip()

# Obtains daily rows from an Open-Meteo payload
def _parse_daily(payload):
    d = (payload or {}).get("daily") or {}
    times = d.get("time") or []
    wmo_codes = d.get("weather_code") or []
    tmins = d.get("temperature_2m_min") or []
    tmaxs = d.get("temperature_2m_max") or []
    precips = d.get("precipitation_sum") or []
    uvmaxs = d.get("uv_index_max") or []
    n = len(times)
    for i in range(n):
        yield {
            "date": times[i] if i < len(times) else None,
            "wmo_code": wmo_codes[i] if i < len(wmo_codes) else None,
            "t_min": tmins[i] if i < len(tmins) else None,
            "t_max": tmaxs[i] if i < len(tmaxs) else None,
            "precip_sum": precips[i] if i < len(precips) else None,
            "uv_max": uvmaxs[i] if i < len(uvmaxs) else None,
        }

# Computes summary stats from daily info
def _summary_from_payload(payload):
    rows = list(_parse_daily(payload))
    n = len(rows)
    if n == 0:
        return {"days": 0, "t_min_avg": None, "t_max_avg": None, "precip_total": None, "uv_max_avg": None}

    tmins = [r["t_min"] for r in rows if r["t_min"] is not None]
    tmaxs = [r["t_max"] for r in rows if r["t_max"] is not None]
    precs = [r["precip_sum"] for r in rows if r["precip_sum"] is not None]
    uvmax = [r["uv_max"] for r in rows if r["uv_max"] is not None]

    t_min_avg = (sum(tmins) / len(tmins)) if tmins else None
    t_max_avg = (sum(tmaxs) / len(tmaxs)) if tmaxs else None
    precip_total = sum(precs) if precs else 0.0
    uv_max_avg = (sum(uvmax) / len(uvmax)) if uvmax else None
    return {"days": n, "t_min_avg": t_min_avg, "t_max_avg": t_max_avg, "precip_total": precip_total, "uv_max_avg": uv_max_avg}

# Returns WeatherRequest rows newest first
def _requests_iter():
    return WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all()

# Returns live weather for a search query
@bp.route('/api/weather')
def api_weather():
    coords = coordinates_from_query(request.args.get('q'))
    if not coords:
        return jsonify({"error": "not_found"}), 404
    lat, lon, display = coords
    payload = fetch_weather(lat, lon)
    return jsonify({"place": display, "data": payload})

# Lists saved locations
@bp.route('/api/locations', methods=['GET'])
def api_locations_list():
    locs = Location.query.order_by(Location.created_at.desc()).all()
    return jsonify([{"id": l.id, "name": l.name, "lat": l.latitude, "lon": l.longitude} for l in locs])

# Creates a saved location
@bp.route('/api/locations', methods=['POST'])
def api_locations_create():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get('name') or '').strip()
    q = (body.get('q') or '').strip()
    if not name or not q:
        return jsonify({"error": "bad_request"}), 400

    coords = coordinates_from_query(q)
    if not coords:
        return jsonify({"error": "not_found"}), 404

    lat, lon, _ = coords
    loc = Location(name=name, latitude=lat, longitude=lon)
    db.session.add(loc)
    db.session.commit()
    return jsonify({"id": loc.id}), 201

# Updates a saved location’s name
@bp.route('/api/locations/<int:loc_id>', methods=['PATCH'])
def api_locations_update(loc_id):
    loc = Location.query.get_or_404(loc_id)
    body = request.get_json(force=True, silent=True) or {}
    if 'name' in body:
        name = (body['name'] or '').strip()
        if name:
            loc.name = name
    db.session.commit()
    return jsonify({"ok": True})

# Deletes a saved location
@bp.route('/api/locations/<int:loc_id>', methods=['DELETE'])
def api_locations_delete(loc_id):
    loc = Location.query.get_or_404(loc_id)
    db.session.delete(loc)
    db.session.commit()
    return jsonify({"ok": True})

# Lists historical requests
@bp.route('/api/requests', methods=['GET'])
def api_requests_list():
    rows = WeatherRequest.query.order_by(WeatherRequest.created_at.desc()).all()
    return jsonify([{
        "id": r.id,
        "name": r.name,
        "display_name": r.display_name,
        "lat": r.latitude,
        "lon": r.longitude,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat()
    } for r in rows])

# Creates a historical request
@bp.route('/api/requests', methods=['POST'])
def api_requests_create():
    body = request.get_json(force=True, silent=True) or {}
    try:
        model = RangeRequest(**body)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    coords = coordinates_from_query(model.q, allow_fuzzy=model.allow_fuzzy)
    if not coords:
        return jsonify({"error": "not_found"}), 404

    lat, lon, display = coords
    payload = fetch_weather_range(lat, lon, model.start_date, model.end_date)
    r = WeatherRequest(
        name=model.name,
        display_name=display,
        latitude=lat,
        longitude=lon,
        start_date=model.start_date,
        end_date=model.end_date,
        payload_json=json.dumps(payload)
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({"id": r.id}), 201

# Returns a historical request with data
@bp.route('/api/requests/<int:req_id>', methods=['GET'])
def api_requests_read(req_id):
    r = WeatherRequest.query.get_or_404(req_id)
    return jsonify({
        "id": r.id,
        "name": r.name,
        "display_name": r.display_name,
        "lat": r.latitude,
        "lon": r.longitude,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat(),
        "data": json.loads(r.payload_json or "{}")
    })

# Updates a historical request and refetches data
@bp.route('/api/requests/<int:req_id>', methods=['PATCH'])
def api_requests_update(req_id):
    r = WeatherRequest.query.get_or_404(req_id)
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or r.name).strip()
    start = body.get("start_date", r.start_date.isoformat())
    end = body.get("end_date", r.end_date.isoformat())

    model = RangeRequest(name=name, q=f"{r.latitude},{r.longitude}", start_date=start, end_date=end)
    r.name = model.name
    r.start_date = model.start_date
    r.end_date = model.end_date

    payload = fetch_weather_range(r.latitude, r.longitude, r.start_date, r.end_date)
    r.payload_json = json.dumps(payload)
    db.session.commit()
    return jsonify({"ok": True})

# Deletes a historical request
@bp.route('/api/requests/<int:req_id>', methods=['DELETE'])
def api_requests_delete(req_id):
    r = WeatherRequest.query.get_or_404(req_id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({"ok": True})

# Exports summaries as JSON
@bp.route('/api/exports/summary.json')
def export_summary_json():
    out = []
    for r in _requests_iter():
        payload = json.loads(r.payload_json or "{}")
        agg = _summary_from_payload(payload)
        out.append({
            "id": r.id,
            "name": r.name,
            "place": r.display_name,
            "lat": r.latitude,
            "lon": r.longitude,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            **agg
        })
    return jsonify(out)

# Exports summaries as CSV
@bp.route('/api/exports/summary.csv')
def export_summary_csv():
    buf = io.StringIO()
    fieldnames = ["id","name","place","lat","lon","start_date","end_date","days","t_min_avg","t_max_avg","precip_total","uv_max_avg"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in _requests_iter():
        payload = json.loads(r.payload_json or "{}")
        agg = _summary_from_payload(payload)
        row = {
            "id": r.id,
            "name": r.name,
            "place": r.display_name,
            "lat": r.latitude,
            "lon": r.longitude,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            **agg
        }
        writer.writerow(row)
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=weather_summary.csv"})

# Exports summaries as Markdown
@bp.route('/api/exports/summary.md')
def export_summary_md():
    lines = [
        "| id | name | place | start | end | days | t_min_avg | t_max_avg | precip_total | uv_max_avg |",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|"
    ]
    for r in _requests_iter():
        payload = json.loads(r.payload_json or "{}")
        agg = _summary_from_payload(payload)
        def fmt(v):
            if isinstance(v, (int, float)):
                return f"{v:.2f}"
            return "—" if v is None else str(v)
        lines.append(
            f"| {r.id} | {r.name} | {r.display_name} | {r.start_date} | {r.end_date} | "
            f"{agg['days']} | {fmt(agg['t_min_avg'])} | {fmt(agg['t_max_avg'])} | {fmt(agg['precip_total'])} | {fmt(agg['uv_max_avg'])} |"
        )
    return Response("\n".join(lines), mimetype="text/markdown",
                    headers={"Content-Disposition": "attachment; filename=weather_summary.md"})

# Exports per-day rows as JSON
@bp.route('/api/exports/daily.json')
def export_daily_json():
    out = []
    for r in _requests_iter():
        payload = json.loads(r.payload_json or "{}")
        for d in _parse_daily(payload):
            out.append({
                "request_id": r.id,
                "name": r.name,
                "place": r.display_name,
                "date": d["date"],
                "wmo_code": d["wmo_code"],
                "wmo_text": WMO.get(d["wmo_code"], "—"),
                "t_min": d["t_min"],
                "t_max": d["t_max"],
                "precip_sum": d["precip_sum"],
                "uv_max": d["uv_max"]
            })
    return jsonify(out)

# Exports per-day rows as CSV
@bp.route('/api/exports/daily.csv')
def export_daily_csv():
    buf = io.StringIO()
    fieldnames = ["request_id","name","place","date","wmo_code","wmo_text","t_min","t_max","precip_sum","uv_max"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in _requests_iter():
        payload = json.loads(r.payload_json or "{}")
        for d in _parse_daily(payload):
            clean_wmo = strip_emojis(WMO.get(d["wmo_code"], "—"))
            writer.writerow({
                "request_id": r.id,
                "name": r.name,
                "place": r.display_name,
                "date": d["date"],
                "wmo_code": d["wmo_code"],
                "wmo_text": clean_wmo,
                "t_min": d["t_min"],
                "t_max": d["t_max"],
                "precip_sum": d["precip_sum"],
                "uv_max": d["uv_max"]
            })
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=weather_daily.csv"})

# Exports per-day rows as Markdown
@bp.route('/api/exports/daily.md')
def export_daily_md():
    lines = [
        "| req_id | name | place | date | wmo | t_min | t_max | precip | uv_max |",
        "|---:|---|---|---|---|---:|---:|---:|---:|"
    ]
    for r in _requests_iter():
        payload = json.loads(r.payload_json or "{}")
        for d in _parse_daily(payload):
            lines.append(
                f"| {r.id} | {r.name} | {r.display_name} | {d['date']} | "
                f"{WMO.get(d['wmo_code'], '—')} | {d['t_min']} | {d['t_max']} | {d['precip_sum']} | {d['uv_max']} |"
            )
    return Response("\n".join(lines), mimetype="text/markdown",
                    headers={"Content-Disposition": "attachment; filename=weather_daily.md"})

# Exports summary for one request as JSON
@bp.route('/api/requests/<int:req_id>/export/summary.json')
def export_one_summary_json(req_id):
    r = WeatherRequest.query.get_or_404(req_id)
    payload = json.loads(r.payload_json or "{}")
    agg = _summary_from_payload(payload)
    return jsonify({
        "id": r.id,
        "name": r.name,
        "place": r.display_name,
        "lat": r.latitude,
        "lon": r.longitude,
        "start_date": r.start_date.isoformat(),
        "end_date": r.end_date.isoformat(),
        **agg
    })

# Exports daily rows for one request as JSON
@bp.route('/api/requests/<int:req_id>/export/daily.json')
def export_one_daily_json(req_id):
    r = WeatherRequest.query.get_or_404(req_id)
    payload = json.loads(r.payload_json or "{}")
    out = []
    for d in _parse_daily(payload):
        out.append({
            "request_id": r.id,
            "name": r.name,
            "place": r.display_name,
            "date": d["date"],
            "wmo_code": d["wmo_code"],
            "wmo_text": WMO.get(d["wmo_code"], "—"),
            "t_min": d["t_min"],
            "t_max": d["t_max"],
            "precip_sum": d["precip_sum"],
            "uv_max": d["uv_max"]
        })
    return jsonify(out)
