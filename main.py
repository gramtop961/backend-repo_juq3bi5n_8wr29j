import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Event, Venue, Category, Bookmark, User

app = FastAPI(title="Kujivinjari API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Kujivinjari API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", None) or ("✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# Helper to convert ObjectId strings safely
class IDModel(BaseModel):
    id: str


def parse_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


# Seed minimal categories if empty (optional helper)
@app.post("/seed/categories")
def seed_categories():
    default = [
        {"name": "Clubs", "slug": "clubs", "icon": "music", "color": "purple"},
        {"name": "Food", "slug": "food", "icon": "utensils", "color": "teal"},
        {"name": "Concerts", "slug": "concerts", "icon": "mic", "color": "purple"},
        {"name": "Plays", "slug": "plays", "icon": "drama", "color": "purple"},
        {"name": "Outdoors", "slug": "outdoors", "icon": "tree", "color": "teal"},
    ]
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    existing = db["category"].count_documents({})
    if existing == 0:
        db["category"].insert_many(default)
    return {"inserted": max(0, len(default) - existing), "total": db["category"].count_documents({})}


# Venues
@app.post("/venues")
def create_venue(venue: Venue):
    venue_id = create_document("venue", venue)
    return {"id": venue_id}


@app.get("/venues")
def list_venues(category: Optional[str] = None, q: Optional[str] = None, limit: int = Query(50, le=200)):
    filter_q = {}
    if category:
        filter_q["category_slug"] = category
    if q:
        filter_q["$text"] = {"$search": q}
    items = get_documents("venue", filter_q or {}, limit)
    for it in items:
        it["id"] = str(it.pop("_id"))
    return items


# Events
@app.post("/events")
def create_event(event: Event):
    event_id = create_document("event", event)
    return {"id": event_id}


@app.get("/events")
def list_events(
    category: Optional[str] = None,
    q: Optional[str] = None,
    free: Optional[bool] = None,
    limit: int = Query(50, le=200)
):
    filter_q = {}
    if category:
        filter_q["category_slug"] = category
    if q:
        filter_q["$text"] = {"$search": q}
    if free is not None:
        filter_q["is_free"] = free
    items = get_documents("event", filter_q or {}, limit)
    for it in items:
        it["id"] = str(it.pop("_id"))
    return items


@app.get("/events/{event_id}")
def get_event(event_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    doc = db["event"].find_one({"_id": parse_object_id(event_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Event not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


# Bookmarks (simple email based for MVP)
@app.post("/bookmarks")
def save_bookmark(bm: Bookmark):
    # prevent duplicates
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    exists = db["bookmark"].find_one({"user_email": bm.user_email, "event_id": bm.event_id})
    if exists:
        return {"status": "exists"}
    bm_id = create_document("bookmark", bm)
    return {"id": bm_id}


@app.get("/bookmarks")
def list_bookmarks(user_email: str):
    items = get_documents("bookmark", {"user_email": user_email}, 200)
    for it in items:
        it["id"] = str(it.pop("_id"))
    return items


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
