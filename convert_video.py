#!/usr/bin/env python3
"""Convert an mp4 (or any video) into a video_<name>.h header for the HeadphoneScreen firmware.

Usage:
    python3 convert_video.py videos/song.mp4 left  [--fps 20] [--quality 6] [--seconds 10]
    python3 convert_video.py videos/other.mp4 right --start 30 --seconds 12

Drop your source videos in the videos/ folder. Writes video_<name>.h into
firmware/HeadphoneScreen/ with <name>_frames, <name>_offsets[], <name>_data[].
The sketch expects the names "left" and "right".
Needs ffmpeg on PATH (brew install ffmpeg).
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKETCH_DIR = HERE / "firmware" / "HeadphoneScreen"
MAX_FRAME = 60 * 1024          # JPEGDEC frame buffer headroom on the board
SOI, EOI = b"\xff\xd8", b"\xff\xd9"


def run_ffmpeg(src, dst, fps, quality, start, seconds):
    vf = ("crop='min(iw,ih)':'min(iw,ih)',scale=240:240:flags=lanczos,"
          f"fps={fps},format=yuvj420p")
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if start:
        cmd += ["-ss", str(start)]
    cmd += ["-i", str(src)]
    if seconds:
        cmd += ["-t", str(seconds)]
    cmd += ["-vf", vf, "-an", "-c:v", "mjpeg", "-q:v", str(quality),
            "-f", "mjpeg", str(dst)]
    subprocess.run(cmd, check=True)


def split_frames(blob):
    frames, pos = [], 0
    while True:
        start = blob.find(SOI, pos)
        if start < 0:
            break
        end = blob.find(EOI, start + 2)
        if end < 0:
            break
        frames.append(blob[start:end + 2])
        pos = end + 2
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("name", help="left or right (which board/ear this clip is for)")
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--quality", type=int, default=6, help="ffmpeg -q:v, 2=best 10=small")
    ap.add_argument("--start", type=float, default=None, help="skip into the video this many seconds")
    ap.add_argument("--seconds", type=float, default=None, help="clip length in seconds")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        mjpeg = Path(tmp) / "clip.mjpeg"
        run_ffmpeg(args.video, mjpeg, args.fps, args.quality, args.start, args.seconds)
        frames = split_frames(mjpeg.read_bytes())

    if not frames:
        sys.exit("no frames decoded")
    biggest = max(len(f) for f in frames)
    if biggest > MAX_FRAME:
        sys.exit(f"largest frame is {biggest} bytes (> {MAX_FRAME}); rerun with a higher --quality number")

    data = b"".join(frames)
    offsets, acc = [], 0
    for f in frames:
        offsets.append(acc)
        acc += len(f)
    offsets.append(acc)

    out = SKETCH_DIR / f"video_{args.name}.h"
    with out.open("w") as fh:
        fh.write(f"// {args.name} video: {len(frames)} frames, 240x240 MJPEG, generated - do not edit\n")
        fh.write("#pragma once\n")
        fh.write(f"const uint32_t {args.name}_frames = {len(frames)};\n")
        fh.write(f"const uint32_t {args.name}_offsets[] = {{{','.join(map(str, offsets))}}};\n")
        fh.write(f"const uint8_t {args.name}_data[] = {{\n")
        for i in range(0, len(data), 32):
            fh.write(",".join(str(b) for b in data[i:i + 32]) + ",\n")
        fh.write("};\n")

    print(f"{out}: {len(frames)} frames @ {args.fps} fps = {len(frames)/args.fps:.1f} s, "
          f"{len(data)/1024/1024:.2f} MB, largest frame {biggest/1024:.1f} KB")


if __name__ == "__main__":
    main()
