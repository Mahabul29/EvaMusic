"""
EvaMusic — Data Models
Defines user profile, preferences, and activity tracking structures.
"""

from datetime import datetime
from database import get_collection


# ═══════════════════════════════════════════════════════════════
# USER PROFILE MODEL
# ═══════════════════════════════════════════════════════════════

class UserProfile:
    """Represents a user's profile in EvaMusic."""

    def __init__(self, user_id, username="", email=None, bio="", 
                 avatar_url=None, display_name=None, 
                 social_links=None, preferences=None):
        self.user_id = user_id
        self.username = username
        self.display_name = display_name or username
        self.email = email
        self.bio = bio or "Music lover 🎵"
        self.avatar_url = avatar_url or "/static/images/avatars/default.png"
        self.social_links = social_links or {
            "instagram": "",
            "twitter": "",
            "youtube": "",
            "spotify": ""
        }
        self.preferences = preferences or {
            "theme": "dark",
            "language": "en",
            "notifications": True,
            "text_size": "medium",
            "accent_color": "#1DB954",  # Spotify green default
            "auto_play": True,
            "download_quality": "high"
        }
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        self.stats = {
            "total_plays": 0,
            "total_favorites": 0,
            "total_playlists": 0,
            "listening_hours": 0.0
        }

    def to_dict(self):
        """Convert profile to dictionary for MongoDB storage."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "email": self.email,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "social_links": self.social_links,
            "preferences": self.preferences,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "stats": self.stats
        }

    @classmethod
    def from_dict(cls, data):
        """Create UserProfile from dictionary (MongoDB document)."""
        profile = cls(
            user_id=data.get("user_id"),
            username=data.get("username", ""),
            email=data.get("email"),
            bio=data.get("bio", "Music lover 🎵"),
            avatar_url=data.get("avatar_url"),
            display_name=data.get("display_name"),
            social_links=data.get("social_links"),
            preferences=data.get("preferences")
        )
        profile.created_at = data.get("created_at", datetime.utcnow())
        profile.last_active = data.get("last_active", datetime.utcnow())
        profile.stats = data.get("stats", profile.stats)
        return profile


# ═══════════════════════════════════════════════════════════════
# AVATAR OPTIONS
# ═══════════════════════════════════════════════════════════════

AVATAR_OPTIONS = [
    "/static/images/avatars/avatar1.png",
    "/static/images/avatars/avatar2.png",
    "/static/images/avatars/avatar3.png",
    "/static/images/avatars/avatar4.png",
    "/static/images/avatars/avatar5.png",
    "/static/images/avatars/avatar6.png",
    "/static/images/avatars/avatar7.png",
    "/static/images/avatars/avatar8.png",
]

THEME_OPTIONS = {
    "dark": {"name": "Dark", "bg": "#121212", "text": "#ffffff", "accent": "#1DB954"},
    "light": {"name": "Light", "bg": "#ffffff", "text": "#121212", "accent": "#1DB954"},
    "amoled": {"name": "AMOLED Black", "bg": "#000000", "text": "#ffffff", "accent": "#1DB954"},
    "ocean": {"name": "Ocean Blue", "bg": "#0a1628", "text": "#e0e7ff", "accent": "#3b82f6"},
    "sunset": {"name": "Sunset Orange", "bg": "#1a0a00", "text": "#fff0e0", "accent": "#f97316"},
    "purple": {"name": "Royal Purple", "bg": "#1a0a1a", "text": "#f0e0ff", "accent": "#a855f7"},
}

ACCENT_COLORS = [
    "#1DB954",  # Green
    "#3b82f6",  # Blue
    "#f97316",  # Orange
    "#ef4444",  # Red
    "#a855f7",  # Purple
    "#ec4899",  # Pink
    "#14b8a6",  # Teal
    "#fbbf24",  # Yellow
]


# ═══════════════════════════════════════════════════════════════
# PROFILE DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════

def create_profile(user_id, username, email=None):
    """Create a new user profile."""
    coll = get_collection("users")
    if not coll:
        return {"success": False, "message": "DB unavailable"}

    try:
        if coll.find_one({"user_id": user_id}):
            return {"success": False, "message": "Profile already exists"}

        profile = UserProfile(user_id=user_id, username=username, email=email)
        coll.insert_one(profile.to_dict())
        return {"success": True, "message": "Profile created"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_profile(user_id):
    """Get user profile by ID."""
    coll = get_collection("users")
    if not coll:
        return None
    try:
        data = coll.find_one({"user_id": user_id}, {"_id": 0})
        if data:
            return UserProfile.from_dict(data)
        return None
    except Exception:
        return None


def update_profile(user_id, updates):
    """Update user profile fields."""
    coll = get_collection("users")
    if not coll:
        return {"success": False, "message": "DB unavailable"}

    try:
        # Only allow specific fields to be updated
        allowed_fields = [
            "username", "display_name", "email", "bio", 
            "avatar_url", "social_links", "preferences"
        ]
        filtered = {k: v for k, v in updates.items() if k in allowed_fields}
        filtered["last_active"] = datetime.utcnow()

        result = coll.update_one(
            {"user_id": user_id},
            {"$set": filtered}
        )

        if result.modified_count > 0 or result.matched_count > 0:
            return {"success": True, "message": "Profile updated"}
        return {"success": False, "message": "Profile not found"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def update_stats(user_id, stat_name, value):
    """Update a specific stat counter."""
    coll = get_collection("users")
    if not coll:
        return
    try:
        coll.update_one(
            {"user_id": user_id},
            {"$inc": {f"stats.{stat_name}": value}, "$set": {"last_active": datetime.utcnow()}}
        )
    except Exception:
        pass


def get_profile_stats(user_id):
    """Get user's listening statistics."""
    from database import get_user_favorites, get_user_playlists, get_recently_played

    profile = get_profile(user_id)
    favorites = get_user_favorites(user_id)
    playlists = get_user_playlists(user_id)
    recent = get_recently_played(user_id, 1000)

    # Calculate listening hours from recently played
    total_seconds = 0
    for song in recent:
        duration = song.get("duration", "0:00")
        try:
            parts = str(duration).split(":")
            if len(parts) == 2:
                total_seconds += int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                total_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            pass

    hours = round(total_seconds / 3600, 1)

    return {
        "total_favorites": len(favorites),
        "total_playlists": len(playlists),
        "total_plays": len(recent),
        "listening_hours": hours,
        "profile": profile.to_dict() if profile else None
    }


def delete_profile(user_id):
    """Delete user profile and all associated data."""
    from database import get_collection as db_get_collection

    try:
        # Delete from all collections
        for name in ["users", "favorites", "recently_played", "playlists", "search_history"]:
            coll = db_get_collection(name)
            if coll:
                coll.delete_many({"user_id": user_id})
        return {"success": True, "message": "Profile deleted"}
    except Exception as e:
        return {"success": False, "message": str(e)}
