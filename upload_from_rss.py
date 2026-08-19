import os
import re
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

TOKEN_PATH = "token.json"

def clean_title(raw):
    raw = raw.strip()
    raw = re.sub(r'[<>|\'\"\\]', '', raw)
    return raw[:100]

def check_and_publish_private_videos(youtube):
    print("🔍 در حال بررسی ویدیوهای کانال برای یافتن موارد Private...")
    
    # گرفتن لیست آخرین ویدیوهای کانال
    request = youtube.search().list(
        part="snippet",
        forMine=True,
        type="video",
        maxResults=20
    )
    response = request.execute()

    count_fixed = 0
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]

        # بررسی وضعیت پابلیک یا پرایوت بودن ویدیو
        video_response = youtube.videos().list(
            part="status",
            id=video_id
        ).execute()
        
        items_status = video_response.get("items", [])
        if items_status:
            status = items_status[0]["status"]["privacyStatus"]
            if status == "private":
                print(f"🔓 ویدیوی پرایوت پیدا شد: '{title}' (ID: {video_id}) -> در حال تغییر به Public...")
                
                # پابلیک کردن ویدیو
                youtube.videos().update(
                    part="status",
                    body={
                        "id": video_id,
                        "status": {
                            "privacyStatus": "public"
                        }
                    }
                ).execute()
                count_fixed += 1
                print("✅ ویدیو با موفقیت پابلیک شد.")

    print(f"🎉 بررسی به پایان رسید. تعداد {count_fixed} ویدیوی پرایوت اصلاح و پابلیک شدند.")

if __name__ == "__main__":
    if not os.path.exists(TOKEN_PATH):
        raise Exception("❌ فایل token.json پیدا نشد!")

    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    youtube = build("youtube", "v3", credentials=creds)
    
    check_and_publish_private_videos(youtube)
