import feedparser
import requests
import os
import re
import json
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
PUBLISHED_FILE = "published_episodes.json"

# --- توابع کمکی ---
def clean_title(raw):
    raw = raw.strip()
    raw = re.sub(r'[<>|\'\"\\]', '', raw)
    return raw[:100]

def is_already_published(title):
    try:
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return title in data.get("published", [])
    except FileNotFoundError:
        return False

def add_to_published(title):
    try:
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"published": []}

    if title not in data["published"]:
        data["published"].append(title)
        with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def video_exists_on_youtube(youtube, title):
    search_response = youtube.search().list(
        part="snippet",
        forMine=True,
        type="video",
        maxResults=10,
        q=title
    ).execute()

    for item in search_response.get("items", []):
        existing_title = item["snippet"]["title"]
        if clean_title(existing_title) == clean_title(title):
            return True
    return False

# --- مرحله ۱: خواندن RSS ---
feed = feedparser.parse(RSS_URL)
items = feed.entries

if not items:
    raise Exception("هیچ اپیزودی در RSS پیدا نشد")

episode = items[0]
title = clean_title(episode.title)

# --- مرحله ۲: بررسی حافظه و یوتیوب ---
if is_already_published(title):
    print("⏭️ این قسمت قبلاً در حافظه ثبت شده. رد شد.")
    exit(0)

creds = Credentials.from_authorized_user_file(TOKEN_PATH)
youtube = build("youtube", "v3", credentials=creds)

if video_exists_on_youtube(youtube, title):
    print("⛔ ویدیویی با این عنوان قبلاً در کانال وجود دارد. آپلود رد شد.")
    add_to_published(title)
    exit(0)

# --- مرحله ۳: آماده‌سازی توضیحات ---
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

# --- مرحله ۴: دانلود فایل صوتی ---
print("⬇️ در حال دانلود فایل صوتی...")
audio_url = episode.enclosures[0].href
audio = requests.get(audio_url)
with open(TEMP_AUDIO, "wb") as f:
    f.write(audio.content)

# --- مرحله ۵: دانلود تصویر کاور ---
raw_image = episode.get("image", feed.feed.get("image", {}))
image_url = raw_image["href"] if isinstance(raw_image, dict) and "href" in raw_image else None

if image_url:
    print("⬇️ در حال دانلود تصویر کاور...")
    img = requests.get(image_url)
    with open(TEMP_IMAGE, "wb") as f:
        f.write(img.content)
else:
    print("⚠️ تصویر کاور پیدا نشد، از تصویر پیش‌فرض استفاده می‌شود")

# --- مرحله ۶: ساخت فایل MP4 ---
print("🎬 در حال ساخت فایل ویدیویی...")
audioclip = AudioFileClip(TEMP_AUDIO)
imageclip = ImageClip(TEMP_IMAGE if os.path.exists(TEMP_IMAGE) else "default.jpg")
imageclip = imageclip.set_duration(audioclip.duration).resize(height=720)
videoclip = imageclip.set_audio(audioclip)
videoclip.write_videofile(OUTPUT_VIDEO, fps=24)

# --- مرحله ۷: آپلود به یوتیوب ---
print("📤 در حال آپلود به یوتیوب...")
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

# --- مرحله ۸: ثبت در حافظه و پاک‌سازی ---
add_to_published(title)
os.remove(TEMP_AUDIO)
if os.path.exists(TEMP_IMAGE):
    os.remove(TEMP_IMAGE)
os.remove(OUTPUT_VIDEO)
