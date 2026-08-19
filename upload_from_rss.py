import os
import json

def test_token():
    token_raw = os.environ.get("YOUTUBE_TOKEN_JSON")
    print("TOKEN RAW:", token_raw)
    
    if not token_raw:
        print("❌ توکن اصلاً پیدا نشد!")
        return

    try:
        data = json.loads(token_raw)
        print("✅ JSON با موفقیت خوانده شد!")
        print("Access Token:", data.get("access_token")[:15] + "...")
        print("Refresh Token:", data.get("refresh_token")[:15] + "...")
    except Exception as e:
        print("❌ خطا در خواندن JSON (توکن فرمتش خراب است یا کاراکتر اضافی دارد):", e)

if __name__ == "__main__":
    test_token()
