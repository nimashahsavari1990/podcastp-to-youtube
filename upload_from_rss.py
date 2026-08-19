import os
import re
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def check_and_publish_private_videos():
    # خواندن توکن از GitHub Secrets
    token_data = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not token_data:
        raise Exception("❌ متغیر YOUTUBE_TOKEN_JSON در Secrets گیت‌هاب پیدا نشد!")

    creds_info = json.loads(token_data)
    creds = Credentials.from_authorized_user_info(creds_info)

    # رفرش خودکار توکن اگر منقضی شده باشد
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    youtube = build("youtube", "v3", credentials=creds)
    
    print("🔍 در حال بررسی ویدیوهای کانال...")
    
    request = youtube.search().list(part="snippet", forMine=True, type="video", maxResults=20)
    response = request.execute()

    count_fixed = 0
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]

        video_response = youtube.videos().list(part="status", id=video_id).execute()
        items_status = video_response.get("items", [])
        
        if items_status:
            status = items_status[0]["status"]["privacyStatus"]
            if status == "private":
                print(f"🔓 ویدیوی پرایوت: '{title}' -> در حال پابلیک کردن...")
                youtube.videos().update(
                    part="status",
                    body={"id": video_id, "status": {"privacyStatus": "public"}}
                ).execute()
                count_fixed += 1
                print("✅ پابلیک شد.")

    print(f"🎉 پایان. تعداد {count_fixed} ویدیو پابلیک شدند.")

if __name__ == "__main__":
    check_and_publish_private_videos()
