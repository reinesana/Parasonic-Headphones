Put your source videos here (mp4, mov, webm, gif - anything ffmpeg reads).
Then, from the HeadphoneScreens folder:

  python3 convert_video.py videos/YOUR_CLIP.mp4 left  --seconds 10
  python3 convert_video.py videos/OTHER_CLIP.mp4 right --seconds 10

Use --start N to begin N seconds into the video. Aim for 10-15 s per ear.
