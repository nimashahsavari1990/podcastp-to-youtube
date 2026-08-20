import os
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def check_and_publish_private_videos():
    print("🔍 در حال بررسی ویدیوهای کانال...")
    
    token_raw = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not token_raw:
        raise Exception("❌ متغیر YOUTUBE_TOKEN_JSON در Secrets گیت‌هاب پیدا نشد!")

    token_dict = json.loads(token_raw)
    
    creds = Credentials(
        token=None,
        refresh_token=token_dict.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=token_dict.get("client_id"),
        client_secret=token_dict.get("client_secret")
    )

    creds.refresh(Request())

    youtube = build("youtube", "v3", credentials=creds)
    
    request = youtube.search().list(
        part="snippet",
        forMine=True,
        type="video",
        maxResults=100
    )
    response = request.execute()

    count_fixed = 0
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]

        video_response = youtube.videos().list(
            part="status",
            id=video_id
        ).execute()
        
        items_status = video_response.get("items", [])
        if items_status:
            status = items_status[0]["status"]["privacyStatus"]
            if status == "private":
                print(f"🔓 ویدیوی پرایوت پیدا شد: '{title}' (ID: {video_id}) -> در حال تغییر به Public...")
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
    check_and_publish_private_videos()
