"""
Database Schemas for Kujivinjari MVP

Each Pydantic model represents a collection in MongoDB. Collection name is the
lowercase class name.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Users (basic placeholder for bookmarks/ownership)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(True, description="Whether user is active")


class Category(BaseModel):
    name: str = Field(..., description="Display name e.g. Clubs, Food, Concerts")
    slug: str = Field(..., description="URL-safe slug e.g. clubs, food")
    icon: Optional[str] = Field(None, description="Optional icon name for UI")
    color: Optional[str] = Field(None, description="Hex or tailwind token")


class VenueLocation(BaseModel):
    type: str = Field("Point", pattern="^Point$", description="GeoJSON type")
    coordinates: List[float] = Field(..., min_items=2, max_items=2, description="[lng, lat]")


class Venue(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    category_slug: Optional[str] = Field(None, description="Links to Category.slug")
    location: Optional[VenueLocation] = None
    images: Optional[List[str]] = Field(default_factory=list)


class Event(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    venue_id: Optional[str] = Field(None, description="Reference to venue _id (string)")
    category_slug: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    is_free: bool = False
    banner_image: Optional[str] = None
    ticket_url: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)


class Bookmark(BaseModel):
    user_email: str
    event_id: str
