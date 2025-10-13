# Imports
from typing import List

def insights_from_payload(payload: dict) -> List[str]:
    tips = []
    cur = payload.get("current") or {}

    # Define weather parameters
    t = cur.get("temperature_2m")         
    feels = cur.get("apparent_temperature")
    rh = cur.get("relative_humidity_2m")   
    wind = cur.get("wind_speed_10m")     
    precip = cur.get("precipitation")     
    uv = cur.get("uv_index")               
    wcode = cur.get("weather_code")        

    # Any precipitation > 0 mm means rain is likely (suggest umbrella)
    if precip and precip > 0:
        tips.append("Pack an umbrella or rain jacket.")

    # UV index >= 6 is considered "high" (recommend sunscreen)
    if uv and uv >= 6:
        tips.append("High UV: wear sunscreen and sunglasses.")

    # Wind >= 35 km/h can feel strong/dangerous 
    if wind and wind >= 35:
        tips.append("Strong winds: secure hats/loose items; caution for cycling.")

    # Temp ≤ 0°C = freezing  (warn about ice and dressing in layers)
    if t is not None and t <= 0:
        tips.append("Freezing temps: dress in layers and watch for ice.")

    # Temp ≥ 30°C = hot weather (hydration advice)
    if t is not None and t >= 30:
        tips.append("Heat alert: hydrate and limit midday activity.")
    
    # "Feels-like" differs from actual temp by >= 4°C  (Provide dressing advice)
    if feels is not None and t is not None and abs(feels - t) >= 4:
        tips.append("Feels-like differs from actual: dress for how it *feels*.")

    # Weather codes 95, 96, 99 = thunderstorm codes found from (Open-Meteo API)
    if wcode in (95, 96, 99):  
        tips.append("Thunderstorms possible: check lightning safety and delays.")

    # If nothing special stands out, provides a generic message
    if not tips:
        tips.append("Weather looks routine. Enjoy your day!")

    return tips
