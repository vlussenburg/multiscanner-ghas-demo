import json
import logging
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, field_validator
from redis import Redis

from app.config import settings

app = FastAPI(title="Location Service", version="1.0.0")
security = HTTPBasic()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

_AUTH_USER = b"me@me.com"
_AUTH_PASS = b"123456"


def authenticate(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    user_ok = secrets.compare_digest(credentials.username.encode(), _AUTH_USER)
    pass_ok = secrets.compare_digest(credentials.password.encode(), _AUTH_PASS)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


class Location(BaseModel):
    latitude: float = Field(..., description="GPS latitude in decimal degrees")
    longitude: float = Field(..., description="GPS longitude in decimal degrees")

    @field_validator("latitude")
    @classmethod
    def _validate_latitude(cls, value: float) -> float:
        if not -90.0 <= value <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def _validate_longitude(cls, value: float) -> float:
        if not -180.0 <= value <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return value


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}


@app.post("/location", responses={400: {"description": "Invalid location"}})
async def receive_location(
    location: Location,
    _: Annotated[str, Depends(authenticate)],
) -> dict:
    redis_client.rpush(
        "locations",
        json.dumps({"latitude": location.latitude, "longitude": location.longitude}),
    )
    redis_client.ltrim("locations", -settings.MAX_LOCATIONS, -1)
    return {"status": "ok"}


@app.get("/locations")
async def get_locations(
    _: Annotated[str, Depends(authenticate)],
) -> dict:
    return {
        "locations": [
            json.loads(loc) for loc in redis_client.lrange("locations", 0, -1)
        ]
    }
