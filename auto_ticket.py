import requests
import time

API_TOKEN = "my_secret_token"
BASE_URL = "http://127.0.0.1:5000"
HEADERS = {"X-API-TOKEN": API_TOKEN}

# 1. 打開活動頁
activity_url = "https://tixcraft.com/ticket/area/25_junwon/19967"  #填入特定藝人活動場次網址
resp = requests.post(f"{BASE_URL}/open_url", headers=HEADERS, json={"url": activity_url})
print("open_url:", resp.json())
time.sleep(2)

# 2. 載入 cookie
resp = requests.post(f"{BASE_URL}/load_cookie", headers=HEADERS)
print("load_cookie:", resp.json())
time.sleep(1)

# 3. 自動刷新等開賣
while True:
    resp = requests.post(f"{BASE_URL}/refresh", headers=HEADERS, json={
        "url": activity_url,
        "interval": 2,
        "trigger_text": "立即訂票"
    })
    print("refresh:", resp.json())
    if resp.json().get("status") == "success":
        break
    time.sleep(1)

# 4. 選票
resp = requests.post(f"{BASE_URL}/select_ticket", headers=HEADERS, json={})
print("select_ticket:", resp.json())
time.sleep(1)

# 5. 選座
resp = requests.post(f"{BASE_URL}/select_seat", headers=HEADERS, json={})
print("select_seat:", resp.json())
time.sleep(1)

# 6. 驗證碼（如有）
# 這部分需你手動截圖驗證碼圖片，然後上傳
# with open("captcha.png", "rb") as f:
#     files = {"captcha": f}
#     resp = requests.post(f"{BASE_URL}/captcha", headers=HEADERS, files=files)
#     print("captcha:", resp.json())