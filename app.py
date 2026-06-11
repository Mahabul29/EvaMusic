from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_session import Session
import requests
import os
import hashlib
from datetime import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize MongoDB
mongo = PyMongo(app)
Session(app)
CORS(app)

# JioSaavn API
JIOSAAVN_API = Config.JIOSAAVN_API_URL

def fetch_api(params):
    params['_format'] = 'json'
    try:
        r = requests.get(JIOSAAVN_API, params=params, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def clean(text):
    return ' '.join(text.split()) if text else 'Unknown'

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = hashlib.md5(os.urandom(32)).hexdigest()[:16]
    return session['user_id']

@app.route('/')
def index():
    return render_template('index.html', koyeb_url=Config.KOYEB_APP_URL)

@app.route('/api/search')
def search():
    q = request.args.get('q', '')
    if not q:
        return jsonify({'error': 'No query'}), 400
    
    data = fetch_api({'__call': 'search.getResults', 'q': q})
    songs = []
    
    if data and 'results' in data:
        for item in data['results'][:20]:
            song_data = {
                'id': item.get('id'),
                'title': clean(item.get('title')),
                'artist': clean(item.get('primary_artists')),
                'image': item.get('image', '').replace('150x150', '500x500')
            }
            songs.append(song_data)
            
            # Save to MongoDB for caching
            db = mongo.db.songs
            db.update_one(
                {'id': song_data['id']},
                {'$set': {**song_data, 'last_updated': datetime.utcnow()}},
                upsert=True
            )
    
    return jsonify({'songs': songs})

@app.route('/api/song/<sid>')
def song_details(sid):
    # Try to get from MongoDB cache first
    db = mongo.db.songs
    cached = db.find_one({'id': sid})
    
    data = fetch_api({'__call': 'song.getDetails', 'pids': sid})
    if not data or sid not in data:
        return jsonify({'error': 'Not found'}), 404
    
    s = data[sid]
    stream = fetch_api({
        '__call': 'song.generateAuthToken',
        'url': s.get('encrypted_media_url', '')
    })
    
    song = {
        'id': sid,
        'title': clean(s.get('title')),
        'artist': clean(s.get('primary_artists')),
        'album': clean(s.get('album')),
        'duration': s.get('duration'),
        'image': s.get('image', '').replace('150x150', '500x500'),
        'stream_url': stream.get('auth_url', '') if stream else ''
    }
    
    # Save to MongoDB
    db.update_one(
        {'id': sid},
        {'$set': {**song, 'last_played': datetime.utcnow()}},
        upsert=True
    )
    
    # Track play count
    user_id = get_user_id()
    db = mongo.db.history
    db.insert_one({
        'user_id': user_id,
        'song_id': sid,
        'song_title': song['title'],
        'played_at': datetime.utcnow()
    })
    
    return jsonify(song)

@app.route('/api/trending')
def trending():
    data = fetch_api({'__call': 'content.getTrending', 'type': 'song'})
    songs = []
    
    if data and 'trending' in data:
        for item in data['trending'][:20]:
            songs.append({
                'id': item.get('id'),
                'title': clean(item.get('title')),
                'artist': clean(item.get('primary_artists')),
                'image': item.get('image', '').replace('150x150', '500x500')
            })
    
    return jsonify({'songs': songs})

@app.route('/api/history')
def get_history():
    user_id = get_user_id()
    db = mongo.db.history
    history = list(db.find({'user_id': user_id}).sort('played_at', -1).limit(50))
    
    for h in history:
        h['_id'] = str(h['_id'])
    
    return jsonify({'history': history})

@app.route('/api/favorite/<sid>', methods=['POST'])
def add_favorite(sid):
    user_id = get_user_id()
    db = mongo.db.favorites
    db.insert_one({
        'user_id': user_id,
        'song_id': sid,
        'added_at': datetime.utcnow()
    })
    return jsonify({'success': True})

@app.route('/api/favorites')
def get_favorites():
    user_id = get_user_id()
    db = mongo.db.favorites
    favorites = list(db.find({'user_id': user_id}))
    
    song_ids = [f['song_id'] for f in favorites]
    songs_db = mongo.db.songs
    songs = list(songs_db.find({'id': {'$in': song_ids}}))
    
    for s in songs:
        s['_id'] = str(s['_id'])
    
    return jsonify({'favorites': songs})

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT)
