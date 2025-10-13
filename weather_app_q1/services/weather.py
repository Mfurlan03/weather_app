

import requests

# This link is where we send a request to get forecast and current weather data.
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Correlating the weather code to emojis for an interpretable visualization for the users
WMO = {
    0: "☀️ Clear", 1: "🌤️ Mostly clear", 2: "⛅ Partly cloudy", 3: "☁️ Overcast",
    45: "🌫️ Fog", 48: "🌫️ Rime fog",
    51: "🌦️ Light drizzle", 53: "🌦️ Drizzle", 55: "🌧️ Dense drizzle",
    56: "🌧️ Freezing drizzle", 57: "🌧️ Heavy freezing drizzle",
    61: "🌦️ Light rain", 63: "🌧️ Rain", 65: "🌧️ Heavy rain",
    66: "🌧️ Freezing rain", 67: "🌧️ Heavy freezing rain",
    71: "🌨️ Light snow", 73: "🌨️ Snow", 75: "❄️ Heavy snow",
    77: "❄️ Snow grains", 80: "🌧️ Rain showers", 81: "🌧️ Showers", 82: "🌧️ Heavy showers",
    85: "🌨️ Snow showers", 86: "🌨️ Heavy snow showers",
    95: "⛈️ Thunderstorm", 96: "⛈️ Thunderstorm (hail)", 99: "⛈️ Severe thunderstorm (hail)"
}

# Gathers all of the weather data from the API
def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "wind_speed_10m",
            "precipitation",
            "weather_code",
            "uv_index",
        ]),
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "uv_index_max",
        ]),
        "forecast_days": 5,
        "timezone": "auto",
    }
    # Sends a request to the Open-Meteo API with the location & fields you asked for
    # Checks if the response is valid
    # Returns the weather data as a Python dictionary your app can use.
    resp = requests.get(FORECAST_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()
