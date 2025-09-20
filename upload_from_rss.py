import feedparser
import requests
import os
import re
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from moviepy.editor import AudioFileClip, ImageClip

# --- تنظیمات اولیه ---
RSS_URL = "https://anchor.fm/s/8940a34c/podcast/rss"
TOKEN_PATH = "token.json"
TEMP_AUDIO = "episode.mp3"
TEMP_IMAGE = "thumbnail.jpg"
OUTPUT_VIDEO = "output.mp4"
LATEST_FILE = "latest_episode.txt"

# --- بررسی آخرین قسمت آپلود شده ---
def get_latest_uploaded():
    if os.path.exists(LATEST_FILE):
        with open(LATEST_FILE, "r") as f:
            return f.read().strip()
    return ""

def set_latest_uploaded(title):
    with open(LATEST_FILE, "w") as f:
        f.write(title.strip())

# --- مرحله ۱: خواندن RSS ---
feed = feedparser.parse(RSS_URL)
items = feed.entries

if not items:
    raise Exception("هیچ اپیزودی در RSS پیدا نشد")

episode = items[0]  # آخرین قسمت

title = episode.title.strip()
title = re.sub(r'[<>|\'\"\\]', '', title)
title = title[:100]
if title == get_latest_uploaded():
    print("⏭️ این قسمت قبلاً آپلود شده. رد شد.")
    exit(0)

# --- مرحله ۲: آماده‌سازی توضیحات ---
raw_description = episode.description
soup = BeautifulSoup(raw_description, "html.parser")

for br in soup.find_all("br"):
    br.replace_with("\n")
for p in soup.find_all("p"):
    p.insert_before("\n")

clean_text = soup.get_text(separator=' ', strip=True)
description = clean_text.replace('\r', '').strip()
description = re.sub(r'[<>|\'\"\\]', '', description)
description = description[:4000]

# --- مرحله ۳: دانلود فایل صوتی ---
print("⬇️ در حال دانلود فایل صوتی...")
audio_url = episode.enclosures[0].href
audio = requests.get(audio_url)
with open(TEMP_AUDIO, "wb") as f:
    f.write(audio.content)

# --- مرحله ۴: دانلود تصویر کاور ---
raw_image = episode.get("image", feed.feed.get("image", {}))
image_url = raw_image["href"] if isinstance(raw_image, dict) and "href" in raw_image else None

if image_url:
    print("⬇️ در حال دانلود تصویر کاور...")
    img = requests.get(image_url)
    with open(TEMP_IMAGE, "wb") as f:
        f.write(img.content)
else:
    print("⚠️ تصویر کاور پیدا نشد، از تصویر پیش‌فرض استفاده می‌شود")

# --- مرحله ۵: ساخت فایل MP4 ---
print("🎬 در حال ساخت فایل ویدیویی...")
audioclip = AudioFileClip(TEMP_AUDIO)
imageclip = ImageClip(TEMP_IMAGE if os.path.exists(TEMP_IMAGE) else "default.jpg")
imageclip = imageclip.set_duration(audioclip.duration).resize(height=720)
videoclip = imageclip.set_audio(audioclip)
videoclip.write_videofile(OUTPUT_VIDEO, fps=24)

# --- مرحله ۶: آپلود به یوتیوب ---
print("📤 در حال آپلود به یوتیوب...")
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
youtube = build("youtube", "v3", credentials=creds)

body = {
    "snippet": {
        "title": title,
        "description": description,
        "tags": ["پادکست", "Anchor", "اتوماتیک"],
        "categoryId": "22"
    },
    "status": {
        "privacyStatus": "public"
    }
}

media = MediaFileUpload(OUTPUT_VIDEO, mimetype="video/mp4", resumable=True)
request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
response = request.execute()

print("✅ آپلود انجام شد! لینک ویدیو:")
print(f"https://www.youtube.com/watch?v={response['id']}")

# --- مرحله ۷: ذخیره عنوان و پاک‌سازی ---
set_latest_uploaded(title)
os.remove(TEMP_AUDIO)
if os.path.exists(TEMP_IMAGE):
    os.remove(TEMP_IMAGE)
os.remove(OUTPUT_VIDEO)

