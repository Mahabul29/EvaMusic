"""
EvaMusic - MongoDB Database Configuration
Handles connection to MongoDB Atlas or local instance
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os

# MongoDB Connection URL
# Replace with your actual MongoDB Atlas URL or local connection string
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://username:password@cluster.mongodb.net/evamusic?retryWrites=true&w=majority")

# Database Name
DB_NAME = "evamusic"

# Collection Names
COLLECTIONS = {
    "users": "users",
    "favorites": "favorites",           # Stores user's favorite songs
    "playlists": "playlists",           # User-created playlists
    "recently_played": "recently_played", # Recently played tracks
    "search_history": "search_history",  # Search queries history
    "downloads": "downloads"             # Offline download tracking
}


def get_db_client():
    """
    Create and return a MongoDB client instance.
    Returns None if connection fails.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Verify connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None


def get_database(client=None):
    """
    Get the EvaMusic database instance.
    Creates a new client if none provided.
    """
    if client is None:
        client = get_db_client()
    if client:
        return client[DB_NAME]
    return None


def get_collection(collection_name, client=None):
    """
    Get a specific collection from the database.
    
    Args:
        collection_name: Name of the collection (use COLLECTIONS dict keys)
        client: Optional MongoDB client instance
    
    Returns:
        Collection object or None
    """
    db = get_database(client)
    if db and collection_name in COLLECTIONS:
        return db[COLLECTIONS[collection_name]]
    return None


# ═══════════════════════════════════════════════════════════════
# FAVORITES COLLECTION OPERATIONS
# ═══════════════════════════════════════════════════════════════

def add_to_favorites(user_id, song_data):
    """
    Add a song to user's favorites.
    
    Args:
        user_id: Unique identifier for the user
        song_data: Dictionary containing song info
            {
                "song_id": "unique_song_id",
                "title": "Song Title",
                "artist": "Artist Name",
                "album": "Album Name",
                "duration": "3:45",
                "image_url": "https://...",
                "audio_url": "https://...",
                "source": "jiosaavn"  # or other music source
            }
    
    Returns:
        dict: Result with success status and message
    """
    collection = get_collection("favorites")
    if not collection:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        # Check if already in favorites
        existing = collection.find_one({
            "user_id": user_id,
            "song_id": song_data.get("song_id")
        })
        
        if existing:
            return {"success": False, "message": "Song already in favorites"}
        
        # Prepare document
        favorite_doc = {
            "user_id": user_id,
            "song_id": song_data.get("song_id"),
            "title": song_data.get("title"),
            "artist": song_data.get("artist"),
            "album": song_data.get("album"),
            "duration": song_data.get("duration"),
            "image_url": song_data.get("image_url"),
            "audio_url": song_data.get("audio_url"),
            "source": song_data.get("source", "jiosaavn"),
            "added_at": __import__('datetime').datetime.utcnow()
        }
        
        result = collection.insert_one(favorite_doc)
        return {
            "success": True,
            "message": "Added to favorites",
            "favorite_id": str(result.inserted_id)
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def remove_from_favorites(user_id, song_id):
    """
    Remove a song from user's favorites.
    
    Args:
        user_id: User's unique ID
        song_id: Song's unique ID
    
    Returns:
        dict: Result with success status
    """
    collection = get_collection("favorites")
    if not collection:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        result = collection.delete_one({
            "user_id": user_id,
            "song_id": song_id
        })
        
        if result.deleted_count > 0:
            return {"success": True, "message": "Removed from favorites"}
        return {"success": False, "message": "Song not found in favorites"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def get_user_favorites(user_id, limit=50, skip=0):
    """
    Get all favorite songs for a user.
    
    Args:
        user_id: User's unique ID
        limit: Maximum number of results (default 50)
        skip: Number of results to skip (for pagination)
    
    Returns:
        list: List of favorite song documents
    """
    collection = get_collection("favorites")
    if not collection:
        return []
    
    try:
        favorites = list(collection.find(
            {"user_id": user_id},
            {"_id": 0}  # Exclude MongoDB _id field
        ).sort("added_at", -1).skip(skip).limit(limit))
        return favorites
    except Exception as e:
        print(f"Error fetching favorites: {e}")
        return []


def is_song_favorited(user_id, song_id):
    """
    Check if a specific song is in user's favorites.
    
    Args:
        user_id: User's unique ID
        song_id: Song's unique ID
    
    Returns:
        bool: True if favorited, False otherwise
    """
    collection = get_collection("favorites")
    if not collection:
        return False
    
    try:
        return collection.find_one({
            "user_id": user_id,
            "song_id": song_id
        }) is not None
    except Exception:
        return False


def toggle_favorite(user_id, song_data):
    """
    Toggle a song in/out of favorites.
    If already favorited, removes it. If not, adds it.
    
    Args:
        user_id: User's unique ID
        song_data: Dictionary with song information
    
    Returns:
        dict: Result with action taken and success status
    """
    song_id = song_data.get("song_id")
    
    if is_song_favorited(user_id, song_id):
        result = remove_from_favorites(user_id, song_id)
        result["action"] = "removed"
        return result
    else:
        result = add_to_favorites(user_id, song_data)
        result["action"] = "added"
        return result


# ═══════════════════════════════════════════════════════════════
# RECENTLY PLAYED COLLECTION OPERATIONS
# ═══════════════════════════════════════════════════════════════

def add_to_recently_played(user_id, song_data):
    """
    Add a song to recently played list.
    Keeps only the last 50 songs per user.
    """
    collection = get_collection("recently_played")
    if not collection:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        # Remove existing entry for this song (to move it to top)
        collection.delete_one({
            "user_id": user_id,
            "song_id": song_data.get("song_id")
        })
        
        # Add new entry
        doc = {
            "user_id": user_id,
            "song_id": song_data.get("song_id"),
            "title": song_data.get("title"),
            "artist": song_data.get("artist"),
            "image_url": song_data.get("image_url"),
            "played_at": __import__('datetime').datetime.utcnow()
        }
        collection.insert_one(doc)
        
        # Keep only last 50 entries per user
        all_recent = list(collection.find(
            {"user_id": user_id}
        ).sort("played_at", -1).skip(50))
        
        for old in all_recent:
            collection.delete_one({"_id": old["_id"]})
        
        return {"success": True, "message": "Added to recently played"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def get_recently_played(user_id, limit=20):
    """Get user's recently played songs."""
    collection = get_collection("recently_played")
    if not collection:
        return []
    
    try:
        return list(collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("played_at", -1).limit(limit))
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
# PLAYLIST COLLECTION OPERATIONS
# ═══════════════════════════════════════════════════════════════

def create_playlist(user_id, name, description=""):
    """Create a new playlist for a user."""
    collection = get_collection("playlists")
    if not collection:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        import uuid
        playlist = {
            "playlist_id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": name,
            "description": description,
            "songs": [],
            "created_at": __import__('datetime').datetime.utcnow(),
            "updated_at": __import__('datetime').datetime.utcnow()
        }
        result = collection.insert_one(playlist)
        return {
            "success": True,
            "message": "Playlist created",
            "playlist_id": playlist["playlist_id"]
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def add_song_to_playlist(user_id, playlist_id, song_data):
    """Add a song to an existing playlist."""
    collection = get_collection("playlists")
    if not collection:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        from bson import ObjectId
        result = collection.update_one(
            {
                "playlist_id": playlist_id,
                "user_id": user_id
            },
            {
                "$push": {"songs": song_data},
                "$set": {"updated_at": __import__('datetime').datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Song added to playlist"}
        return {"success": False, "message": "Playlist not found"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def get_user_playlists(user_id):
    """Get all playlists for a user."""
    collection = get_collection("playlists")
    if not collection:
        return []
    
    try:
        return list(collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1))
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
# SEARCH HISTORY
# ═══════════════════════════════════════════════════════════════

def save_search_query(user_id, query):
    """Save a search query to history."""
    collection = get_collection("search_history")
    if not collection:
        return
    
    try:
        # Remove duplicate
        collection.delete_one({"user_id": user_id, "query": query})
        
        collection.insert_one({
            "user_id": user_id,
            "query": query,
            "searched_at": __import__('datetime').datetime.utcnow()
        })
        
        # Keep only last 20 searches
        old = list(collection.find(
            {"user_id": user_id}
        ).sort("searched_at", -1).skip(20))
        for o in old:
            collection.delete_one({"_id": o["_id"]})
    except Exception:
        pass


def get_search_history(user_id, limit=10):
    """Get user's recent search history."""
    collection = get_collection("search_history")
    if not collection:
        return []
    
    try:
        return list(collection.find(
            {"user_id": user_id},
            {"_id": 0, "query": 1}
        ).sort("searched_at", -1).limit(limit))
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def create_user(user_id, username, email=None):
    """Create a new user document."""
    collection = get_collection("users")
    if not collection:
        return {"success": False, "message": "Database connection failed"}
    
    try:
        existing = collection.find_one({"user_id": user_id})
        if existing:
            return {"success": False, "message": "User already exists"}
        
        user = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "created_at": __import__('datetime').datetime.utcnow(),
            "last_active": __import__('datetime').datetime.utcnow(),
            "preferences": {
                "theme": "dark",
                "language": "en",
                "notifications": True
            }
        }
        collection.insert_one(user)
        return {"success": True, "message": "User created"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def update_user_activity(user_id):
    """Update user's last active timestamp."""
    collection = get_collection("users")
    if not collection:
        return
    
    try:
        collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": __import__('datetime').datetime.utcnow()}}
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# DATABASE HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

def check_db_health():
    """
    Check if MongoDB connection is healthy.
    Returns status dictionary.
    """
    client = get_db_client()
    if not client:
        return {
            "status": "unhealthy",
            "connected": False,
            "message": "Cannot connect to MongoDB"
        }
    
    try:
        db = client[DB_NAME]
        collections = db.list_collection_names()
        return {
            "status": "healthy",
            "connected": True,
            "database": DB_NAME,
            "collections": collections,
            "message": "MongoDB connection is active"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": True,
            "message": f"Connected but error: {str(e)}"
        }


# Initialize database (create indexes)
def init_db():
    """
    Initialize database with indexes for better performance.
    Call this once when your app starts.
    """
    client = get_db_client()
    if not client:
        print("❌ Cannot initialize database - connection failed")
        return False
    
    db = client[DB_NAME]
    
    # Create indexes
    db[COLLECTIONS["favorites"]].create_index([("user_id", 1), ("song_id", 1)], unique=True)
    db[COLLECTIONS["favorites"]].create_index([("user_id", 1), ("added_at", -1)])
    db[COLLECTIONS["recently_played"]].create_index([("user_id", 1), ("played_at", -1)])
    db[COLLECTIONS["playlists"]].create_index("playlist_id", unique=True)
    db[COLLECTIONS["playlists"]].create_index([("user_id", 1)])
    db[COLLECTIONS["search_history"]].create_index([("user_id", 1), ("searched_at", -1)])
    db[COLLECTIONS["users"]].create_index("user_id", unique=True)
    
    print("✅ Database initialized with indexes")
    return True


if __name__ == "__main__":
    # Test the connection
    print("Testing MongoDB connection...")
    health = check_db_health()
    print(health)
      
