import feedparser
import requests
import os
import subprocess
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# تنظیمات اولیه
RSS_FEED = "https://anchor.fm/s/8940a34c/podcast/rss"
VIDEO_OUTPUT = "output.mp4"
IMAGE_FILE = "cover.jpg"
AUDIO_FILE = "audio.mp3"

# خواندن فید
feed = feedparser.parse(RSS_FEED)
latest = feed.entries[0]

title = latest.title
description = latest.description
audio_url = latest.enclosures[0].href
image_url = latest.get("image", {}).get("href") or latest.get("itunes_image", {}).get("href")

# دانلود فایل‌ها
with open(AUDIO_FILE, "wb") as f:
    f.write(requests.get(audio_url).content)

with open(IMAGE_FILE, "wb") as f:
    f.write(requests.get(image_url).content)

# ساخت ویدیو با FFmpeg
subprocess.run([
    "ffmpeg", "-loop", "1", "-i", IMAGE_FILE,
    "-i", AUDIO_FILE, "-c:v", "libx264", "-c:a", "aac",
    "-b:a", "192k", "-shortest", VIDEO_OUTPUT
])

# آپلود به YouTube
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
credentials = flow.run_console()
youtube = build("youtube", "v3", credentials=credentials)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["podcast", "anchor"],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    },
    media_body=VIDEO_OUTPUT
)
response = request.execute()
print("Uploaded:", response["id"])
