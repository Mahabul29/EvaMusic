"""
EvaMusic — Smart Queue Refresh
When a user skips a song it is removed from the active queue
and does NOT appear in the next auto-loaded batch.
"""

import json
import random
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session

import database as db
from user.trackuser import on_song_skipped, on_song_played, get_disliked_songs

refresh_bp = Blueprint("refresh", __name__)


# ═══════════════════════════════════════════════════════════════
# SESSION QUEUE HELPERS
# ═══════════════════════════════════════════════════════════════

_SESSION_QUEUE_KEY   = "eva_queue"
_SESSION_SKIPPED_KEY = "eva_session_skips"


def _get_queue() -> list:
    return session.get(_SESSION_QUEUE_KEY, [])


def _save_queue(queue: list):
    session[_SESSION_QUEUE_KEY] = queue
    session.modified = True


def _get_session_skips() -> set:
    return set(session.get(_SESSION_SKIPPED_KEY, []))


def _add_session_skip(song_id: str):
    skips = list(_get_session_skips())
    if song_id not in skips:
        skips.append(song_id)
    session[_SESSION_SKIPPED_KEY] = skips[-200:]
    session.modified = True


# ═══════════════════════════════════════════════════════════════
# CORE QUEUE LOGIC
# ═══════════════════════════════════════════════════════════════

def set_queue(songs: list) -> dict:
    skips    = _get_session_skips()
    filtered = [
        s for s in songs
        if (s.get("song_id") or s.get("id", "")) not in skips
    ]
    _save_queue(filtered)
    return {"success": True, "queue_length": len(filtered)}


def skip_current_song(user_id: str, song: dict, listen_seconds: int = 3) -> dict:
    song_id = song.get("song_id") or song.get("id", "")

    if user_id and song_id:
        on_song_skipped(user_id, song, listen_seconds)
        _add_session_skip(song_id)

    queue = _get_queue()
    queue = [s for s in queue if (s.get("song_id") or s.get("id", "")) != song_id]
    _save_queue(queue)

    next_song = queue[0] if queue else None
    return {
        "success":    True,
        "next_song":  next_song,
        "queue_left": len(queue),
    }


def get_next_song(user_id: str, current_song_id: str = None) -> dict:
    queue = _get_queue()

    if current_song_id:
        queue = [s for s in queue if (s.get("song_id") or s.get("id", "")) != current_song_id]
        _save_queue(queue)

    next_song = queue[0] if queue else None
    return {
        "next_song":  next_song,
        "queue_left": len(queue),
    }


def peek_queue(limit: int = 5) -> list:
    return _get_queue()[:limit]


def clear_session_skips():
    session.pop(_SESSION_SKIPPED_KEY, None)
    session.pop(_SESSION_QUEUE_KEY, None)
    session.modified = True


def refresh_queue_with_suggestions(user_id: str, candidate_songs: list) -> dict:
    from suggest import get_suggestions_for_user

    skips     = _get_session_skips()
    db_skips  = set(get_disliked_songs(user_id))
    all_skips = skips | db_skips

    fresh_candidates = [
        s for s in candidate_songs
        if (s.get("song_id") or s.get("id", "")) not in all_skips
    ]

    suggested = get_suggestions_for_user(user_id, fresh_candidates, limit=20)
    _save_queue(suggested)

    return {
        "success":      True,
        "refreshed":    True,
        "queue_length": len(suggested),
        "skips_total":  len(all_skips),
    }


# ═══════════════════════════════════════════════════════════════
# FLASK API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@refresh_bp.route("/api/queue/set", methods=["POST"])
def api_set_queue():
    data  = request.get_json(silent=True) or {}
    songs = data.get("songs", [])
    result = set_queue(songs)
    return jsonify(result)


@refresh_bp.route("/api/queue/skip", methods=["POST"])
def api_skip_song():
    from app import get_user_id
    user_id        = get_user_id()
    data           = request.get_json(silent=True) or {}
    listen_seconds = int(data.get("listen_seconds", 3))
    result = skip_current_song(user_id, data, listen_seconds)
    return jsonify(result)


@refresh_bp.route("/api/queue/next", methods=["POST"])
def api_next_song():
    from app import get_user_id
    user_id         = get_user_id()
    data            = request.get_json(silent=True) or {}
    current_song_id = data.get("current_song_id", "")
    result          = get_next_song(user_id, current_song_id)

    if result["queue_left"] < 3:
        candidate_songs = data.get("candidates", [])
        if candidate_songs:
            refresh_queue_with_suggestions(user_id, candidate_songs)

    return jsonify(result)


@refresh_bp.route("/api/queue/peek")
def api_peek_queue():
    limit = request.args.get("limit", 5, type=int)
    return jsonify(peek_queue(limit))


@refresh_bp.route("/api/queue/refresh", methods=["POST"])
def api_refresh_queue():
    from app import get_user_id
    user_id    = get_user_id()
    data       = request.get_json(silent=True) or {}
    candidates = data.get("candidates", [])

    if not candidates:
        return jsonify({"success": False, "message": "No candidate songs provided"}), 400

    result = refresh_queue_with_suggestions(user_id, candidates)
    return jsonify(result)


@refresh_bp.route("/api/queue/played", methods=["POST"])
def api_song_played():
    from app import get_user_id
    user_id        = get_user_id()
    data           = request.get_json(silent=True) or {}
    listen_seconds = int(data.get("listen_seconds", 60))

    on_song_played(user_id, data, listen_seconds)
    db.add_to_recently_played(user_id, {
        "song_id":   data.get("song_id") or data.get("id", ""),
        "title":     data.get("title", "Unknown"),
        "artist":    data.get("artist", "Unknown"),
        "image_url": data.get("image_url") or data.get("image", ""),
        "played_at": datetime.now(timezone.utc).isoformat(),
    })
    return jsonify({"success": True})
        
