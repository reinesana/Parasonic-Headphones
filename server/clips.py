"""Turn a Canvas mp4 or an album-art image into a 240x240 MJPEG clip the boards can play.

Same filter chain as convert_video.py, written as <clips_dir>/<track_id>.mjpeg.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests


def _find_ffmpeg():
    if path := os.environ.get("FFMPEG") or shutil.which("ffmpeg"):
        return path
    import imageio_ffmpeg                    # bundled static binary, pip install imageio-ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


FFMPEG = _find_ffmpeg()
FPS = 20
QUALITY = 7           # ffmpeg -q:v; 2 best .. 10 smallest
MAX_FRAME = 60 * 1024
ART_SECONDS = 8       # length of the album-art zoom loop
SQUARE = "crop='min(iw,ih)':'min(iw,ih)',scale=240:240:flags=lanczos"


def _ffmpeg(args):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args], check=True)


def _download(url, dest):
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)


def _check(path):
    """Guard against frames too big for the board; re-encode smaller if needed."""
    data = Path(path).read_bytes()
    biggest, pos = 0, 0
    while (start := data.find(b"\xff\xd8", pos)) >= 0:
        end = data.find(b"\xff\xd9", start + 2)
        if end < 0:
            break
        biggest = max(biggest, end + 2 - start)
        pos = end + 2
    return biggest


def canvas_to_clip(mp4_url, out_path, quality=QUALITY):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "canvas.mp4"
        _download(mp4_url, src)
        _ffmpeg(["-i", str(src), "-vf", f"{SQUARE},fps={FPS},format=yuvj420p",
                 "-an", "-c:v", "mjpeg", "-q:v", str(quality), "-f", "mjpeg", str(out_path)])
    if _check(out_path) > MAX_FRAME and quality < 12:
        return canvas_to_clip(mp4_url, out_path, quality + 2)
    return out_path


def art_to_clip(image_url, out_path, quality=QUALITY):
    """Slow Ken-Burns zoom on the album art so the ear without a Canvas still moves."""
    frames = FPS * ART_SECONDS
    # zoom in over the first half, back out over the second half, so it loops cleanly
    zoom = f"if(lt(on,{frames // 2}),1+0.12*on/{frames // 2},1.12-0.12*(on-{frames // 2})/{frames // 2})"
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "art.jpg"
        _download(image_url, src)
        _ffmpeg(["-loop", "1", "-i", str(src), "-frames:v", str(frames),
                 "-vf", f"{SQUARE},scale=960:960,zoompan=z='{zoom}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        f":s=240x240:fps={FPS},format=yuvj420p",
                 "-an", "-c:v", "mjpeg", "-q:v", str(quality), "-f", "mjpeg", str(out_path)])
    if _check(out_path) > MAX_FRAME and quality < 12:
        return art_to_clip(image_url, out_path, quality + 2)
    return out_path


if __name__ == "__main__":
    import sys
    url, out = sys.argv[1], sys.argv[2]
    (canvas_to_clip if url.endswith(".mp4") else art_to_clip)(url, out)
    print(out, Path(out).stat().st_size // 1024, "KB, largest frame", _check(out) // 1024, "KB")
