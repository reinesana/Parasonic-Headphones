"""Companion server: watches what you're playing on Spotify and serves a matching clip.

  GET /now            -> {"track_id", "title", "artist", "clip", "source", "playing"}
  GET /clips/<id>     -> the MJPEG file for that track
  GET /health

Run:  .venv/bin/python server.py   (first run opens a browser for Spotify login)
"""
import logging
import os
import threading
import time
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from spotipy.oauth2 import SpotifyOAuth

from canvas import CanvasClient
from clips import art_to_clip, canvas_to_clip

load_dotenv()
log = logging.getLogger("headphones")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

HERE = Path(__file__).resolve().parent
CLIPS = HERE / "clips"
CLIPS.mkdir(exist_ok=True)
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", 3))
PREFETCH = int(os.environ.get("PREFETCH", 2))     # how many upcoming queue tracks to prepare
PORT = int(os.environ.get("PORT", 8787))

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
    redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
    scope="user-read-currently-playing user-read-playback-state",
    cache_path=str(HERE / ".spotify_cache"),
    open_browser=True,
))
canvas = CanvasClient(os.environ["SP_DC"])

state = {"track_id": None, "title": None, "artist": None, "clip": None, "source": None, "playing": False}
sources = {}            # track_id -> "canvas" | "art"
building = set()
lock = threading.Lock()


def ensure_clip(track):
    """Make sure <clips>/<id>.mjpeg exists for this track. Returns its source type."""
    tid = track["id"]
    out = CLIPS / f"{tid}.mjpeg"
    if out.exists() and tid in sources:
        return sources[tid]
    with lock:
        if tid in building:
            return None
        building.add(tid)
    try:
        url = None
        try:
            url = canvas.canvas_url(tid)
        except Exception as e:
            log.warning("canvas lookup failed for %s: %s", tid, e)
        tmp = out.with_suffix(".part")
        if url:
            canvas_to_clip(url, tmp)
            src = "canvas"
        else:
            images = track["album"]["images"]
            art_to_clip(images[0]["url"], tmp)
            src = "art"
        tmp.replace(out)
        sources[tid] = src
        log.info("clip ready: %s - %s [%s] %d KB", track["artists"][0]["name"], track["name"], src,
                 out.stat().st_size // 1024)
        return src
    except Exception as e:
        log.error("clip build failed for %s: %s", tid, e)
        return None
    finally:
        with lock:
            building.discard(tid)


def prefetch_queue():
    try:
        queue = sp.queue().get("queue", [])[:PREFETCH]
    except Exception as e:
        log.debug("queue fetch failed: %s", e)
        return
    for track in queue:
        if track and track.get("type") == "track" and not (CLIPS / f"{track['id']}.mjpeg").exists():
            threading.Thread(target=ensure_clip, args=(track,), daemon=True).start()


def watcher():
    last_id = None
    while True:
        try:
            cur = sp.current_playback(additional_types="track")
            item = cur.get("item") if cur else None
            playing = bool(cur and cur.get("is_playing"))
            if item and item.get("type") == "track":
                if item["id"] != last_id:
                    last_id = item["id"]
                    log.info("now playing: %s - %s", item["artists"][0]["name"], item["name"])
                    src = ensure_clip(item)
                    state.update(track_id=item["id"], title=item["name"],
                                 artist=", ".join(a["name"] for a in item["artists"]),
                                 clip=f"/clips/{item['id']}.mjpeg" if src else None, source=src)
                    prefetch_queue()
                elif state["clip"] is None and (CLIPS / f"{item['id']}.mjpeg").exists():
                    state.update(clip=f"/clips/{item['id']}.mjpeg", source=sources.get(item["id"]))
            state["playing"] = playing
        except Exception as e:
            log.warning("poll failed: %s", e)
        time.sleep(POLL_SECONDS)


app = Flask(__name__)


@app.get("/now")
def now():
    return jsonify(state)


@app.get("/clips/<track_id>")
def clip(track_id):
    return send_from_directory(CLIPS, f"{track_id}.mjpeg", mimetype="application/octet-stream")


@app.get("/health")
def health():
    return {"ok": True, "clips": len(list(CLIPS.glob("*.mjpeg")))}


if __name__ == "__main__":
    sp.current_user()      # triggers the one-time browser login before the server starts
    threading.Thread(target=watcher, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
