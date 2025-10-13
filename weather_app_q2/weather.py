import requests
from datetime import date

# Defined base URL for the Open-Meteo weather API
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Defined weather codes mapped to descriptions
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
# Fetch current and 5-day forecast weather data for given coordinates.
def fetch_weather(lat: float, lon: float) -> dict:

    params = {
        "latitude": lat,
        "longitude": lon,
        # Ask for current weather details
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "wind_speed_10m",
            "precipitation",
            "weather_code",
            "uv_index",
        ]),
        # Ask for daily summaries 
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "uv_index_max",
        ]),
        # Returns forecast range to 5 days and matches user's timezone
        "forecast_days": 5, 
        "timezone": "auto", 
    }
    # Make the API request and handle potential errors 
    resp = requests.get(FORECAST_URL, params=params, timeout=10)
    resp.raise_for_status()  
    return resp.json()  

# Fetch daily weather data for a specific date range.
def fetch_weather_range(lat: float, lon: float, start: date, end: date) -> dict:

    params = {
        "latitude": lat,
        "longitude": lon,
        # Request only daily metrics
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "uv_index_max",
        ]),
        # Format start date and end date
        "start_date": start.isoformat(),  
        "end_date": end.isoformat(),      
        "timezone": "auto",
    }
    # Call the API
    resp = requests.get(FORECAST_URL, params=params, timeout=10)
    resp.raise_for_status()  
    return resp.json()  
