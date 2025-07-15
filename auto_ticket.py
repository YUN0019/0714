#客戶端腳本
#連接API _demo.py

#3️⃣ 如何改成其他藝人/活動？
#只要修改 auto_ticket.py 開頭的參數：
#Apply to auto_ticket....
#即可搶不同活動的票！
#測試存取1231212131312

import requests
import sys
import time

API_TOKEN = "my_secret_token"
BASE_URL = "http://127.0.0.1:5000"
HEADERS = {"X-API-TOKEN": API_TOKEN}

# ====== 參數設定 ======
ARTIST_KEYWORD = "鄭準元JUNG JUNWON《THE ONE DAY》台北見面會"
AREA_KEYWORDS = ["A區"]
PRICE_KEYWORDS = ["5400"]
TICKET_COUNT = 1
EVENT_URL = "https://tixcraft.com/activity/detail/25_junwon"  # 若有活動頁網址可直接填入，否則留空

# ====== API 呼叫工具函式 ======
def call_api(endpoint, payload=None):
    try:
        resp = requests.post(f"{BASE_URL}/{endpoint}", headers=HEADERS, json=payload or {})
        data = resp.json()
        print(f"{endpoint} 回傳：", data)
        if data.get('status') != 'success':
            print(f"❌ {endpoint} 失敗，訊息：{data.get('message')}")
            # 只要不是 solve_captcha，才 exit
            if endpoint != "solve_captcha":
                sys.exit(1)
        return data
    except Exception as e:
        print(f"❌ 呼叫 {endpoint} 發生例外：{e}")
        if endpoint != "solve_captcha":
            sys.exit(1)

# ====== 主流程 ======
def main():
    # 1. 載入 cookie（如有）
    resp = call_api("load_cookie")
    if resp.get('status') != 'success':
        print("⚠️ Cookie 載入失敗，請於瀏覽器手動登入帳號，登入完成後按 Enter...")
        input()
        call_api("save_cookie")
        print("✅ Cookie 已儲存，後續流程將自動化...")
        time.sleep(1)

    # 2. 跳轉活動頁或搜尋
    if EVENT_URL:
        call_api("goto_event_page", {"url": EVENT_URL})
        time.sleep(2)
    else:
        call_api("search_event", {"keyword": ARTIST_KEYWORD})
        time.sleep(2)
        call_api("enter_event_detail")
        time.sleep(2)

    # 3. 點擊立即購票
    call_api("click_buy_now")
    time.sleep(2)

    # 4. 選擇區域/價格（自動比對關鍵字）
    call_api("select_area_price", {"area_keywords": AREA_KEYWORDS, "price_keywords": PRICE_KEYWORDS})
    time.sleep(2)

    # 5. 直接選票數（跳過 select_area_price）
    call_api("select_ticket_count", {"count": TICKET_COUNT})
    time.sleep(2)

    # 6. 辨識驗證碼
    call_api("solve_captcha")
    time.sleep(2)

    # 7. 勾選同意條款
    call_api("agree_terms")
    time.sleep(1)

    # 8. 點擊確認張數
    call_api("confirm_ticket")
    print("🎉 全部流程執行完畢，請於瀏覽器確認結帳頁面！")

if __name__ == "__main__":
    main()

