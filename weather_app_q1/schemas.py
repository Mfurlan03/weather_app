# Why Pydantic?
# I use Pydantic here because it gives me easy validation rules and friendly error message.
# I had to some research behind Pydantic vs Marshmallow 
# and it seems Pydantic is the most modern and user-friendly.

from typing import Optional
from pydantic import BaseModel, field_validator

# Makes sure values are within real latitude/longitude ranges.
def is_latlon(q: str) -> bool:
    try:
        lat_str, lon_str = q.split(",")
        lat, lon = float(lat_str), float(lon_str)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except Exception:
        return False


class SearchQuery(BaseModel):
    
    # User input (city, landmark, postal code, or coordinates) 
    q: Optional[str] = None

    # Validate the query while also providing friendly error messages.
    @field_validator("q")
    @classmethod
    def strip_and_limit(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 120:
            raise ValueError("Query too long (max 120 chars).")
        return v

    # Checks if the query is lat/lon
    def is_coordinates(self) -> bool:
        return bool(self.q and is_latlon(self.q))



