import requests
import time     # 修改到 再問AI　關於搶票位置用中文有甚麼問題的部分！

API_TOKEN = "my_secret_token"
BASE_URL = "http://127.0.0.1:5000"
HEADERS = {"X-API-TOKEN": API_TOKEN}

# 1. 打開活動主頁
activity_url = "https://tixcraft.com/activity/detail/25_junwon"  # 請填入正確活動主頁網址

def safe_post(url, **kwargs):
    try:
        resp = requests.post(url, headers=HEADERS, timeout=10, **kwargs)
        resp.raise_for_status()
        data = resp.json()
        print(f"{url.split('/')[-1]}:", data)
        return data
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
        return None

# 打開活動頁
safe_post(f"{BASE_URL}/open_url", json={"url": activity_url})
time.sleep(2)

# 載入 cookie
safe_post(f"{BASE_URL}/load_cookie")
time.sleep(1)

# 自動刷新等開賣
while True:
    result = safe_post(f"{BASE_URL}/refresh", json={
        "url": activity_url,
        "interval": 2,
        "trigger_text": "立即訂票"
    })
    if result and result.get("status") == "success":
        break
    time.sleep(1)

# 選特定票種與張數
ticket_type_value = "A區5400"  # 這個 value 請用 F12 工具查票種下拉選單的 value
quantity = 2
safe_post(f"{BASE_URL}/select_ticket", json={
    "ticket_type_value": ticket_type_value,
    "quantity": quantity
})
time.sleep(1)

# 選特定座位（請根據實際 selector 調整）
seat_selector = ".area-seat[data-seat='A1']"  # 這個 selector 請用 F12 工具查座位元素
safe_post(f"{BASE_URL}/select_seat", json={
    "seat_selector": seat_selector
})
time.sleep(1)

# 驗證碼處理（如有）
print("如遇到驗證碼，請手動截圖並上傳圖片，或在此處加入自動上傳程式碼。")
# with open("captcha.png", "rb") as f:
#     files = {"captcha": f}
#     resp = requests.post(f"{BASE_URL}/captcha", headers=HEADERS, files=files)
#     print("captcha:", resp.json())

