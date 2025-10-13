from typing import Optional
from datetime import date, timedelta
from pydantic import BaseModel, field_validator, ConfigDict


# Quickly check if latitude and longitude are within actual bounds
def is_latlon(q: str) -> bool:
    try:
        lat_str, lon_str = q.split(",")
        lat, lon = float(lat_str), float(lon_str)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except Exception:
        return False

# Represents what a user types into the search box (like a city name, landmark, postal code, or coordinates)
class SearchQuery(BaseModel):
    q: Optional[str] = None

    @field_validator("q")
    @classmethod
    def strip_and_limit(cls, v: Optional[str]) -> Optional[str]:
        # Trim spaces and enforce a reasonable query size
        if v is None:
            return v
        v = v.strip()
        if len(v) > 120:
            raise ValueError("Query too long (max 120 chars).")
        return v

    # Checks if the user input is written as coordinates (like "43.7,-79.4")
    def is_coordinates(self) -> bool:
        return bool(self.q and is_latlon(self.q))


# Define date request and validation
class RangeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # name: user label
    # q: location query (city/landmark OR 'lat,lon')
    # start_date, end_date: date range (max 31 days, end ≤ 16 days in future)
    # allow_fuzzy: relax place-name matching
    name: str
    q: str
    start_date: date
    end_date: date
    allow_fuzzy: bool = True

    # Ensures the name is provided and within length limit
    @field_validator("name")
    @classmethod
    def name_nonempty(cls, v: str) -> str:
        if not v or len(v) > 160:
            raise ValueError("Name required, max 160 chars.")
        return v

    # Ensures query string is provided and within length limit
    @field_validator("q")
    @classmethod
    def q_limit(cls, v: str) -> str:
        if not v or len(v) > 160:
            raise ValueError("Query required, max 160 chars.")
        return v

    # Ensures that date range is logical and within bounds
    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end: date, info) -> date:
        start: date = info.data.get("start_date")

        if not start or not end:
            raise ValueError("Both start and end dates are required.")

        if end < start:
            raise ValueError("End date must be on or after the start date.")

        if (end - start).days > 31:
            raise ValueError("Date range too large, maximum 31 days allowed.")

        today = date.today()
        max_future = today + timedelta(days=16)
        if end > max_future:
            raise ValueError("End date can't be more than 16 days in the future.")

        return end

