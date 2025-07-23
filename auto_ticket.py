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

def run_auto_ticket(EVENT_URL, ARTIST_KEYWORD, AREA_KEYWORDS, PRICE_KEYWORDS, TICKET_COUNT):
    # 1. 載入 cookie（如有）
    resp = call_api("load_cookie")
    if not resp or resp.get('status') != 'success':
        print("❌ Cookie 載入失敗，請於瀏覽器手動登入帳號，登入完成後按 Enter...")
        return {'status': 'error', 'message': 'Cookie 載入失敗，請手動登入'}
    # 2. 跳轉活動頁或搜尋
    if EVENT_URL:
        resp = call_api("goto_event_page", {"url": EVENT_URL})
        time.sleep(2)
        if not resp or resp.get('status') != 'success':
            print(f"❌ 跳轉活動頁失敗: {resp.get('message') if resp else '無回應'}")
            return {'status': 'error', 'message': '跳轉活動頁失敗'}
    elif ARTIST_KEYWORD:
        resp = call_api("search_event", {"keyword": ARTIST_KEYWORD})
        time.sleep(2)
        if not resp or resp.get('status') != 'success':
            print(f"❌ 搜尋活動失敗: {resp.get('message') if resp else '無回應'}")
            return {'status': 'error', 'message': '搜尋活動失敗'}
        resp = call_api("enter_event_detail")
        time.sleep(2)
        if not resp or resp.get('status') != 'success':
            print(f"❌ 進入活動詳情頁失敗: {resp.get('message') if resp else '無回應'}")
            return {'status': 'error', 'message': '進入活動詳情頁失敗'}
    else:
        print('❌ 缺少活動網址或關鍵字')
        return {'status': 'error', 'message': '缺少活動網址或關鍵字'}
    # 3. 點擊立即購票
    resp = call_api("click_buy_now")
    time.sleep(2)
    if not resp or resp.get('status') != 'success':
        print(f"❌ 點擊立即購票失敗: {resp.get('message') if resp else '無回應'}")
        return {'status': 'error', 'message': '點擊立即購票失敗'}
    # 4. 選擇區域/價格（自動比對關鍵字）
    resp = call_api("select_area_price", {"area_keywords": AREA_KEYWORDS, "price_keywords": PRICE_KEYWORDS})
    time.sleep(2)
    if not resp or resp.get('status') != 'success':
        print(f"❌ 選擇區域/價格失敗: {resp.get('message') if resp else '無回應'}")
        return {'status': 'error', 'message': '選擇區域/價格失敗'}
    # 5. 直接選票數（跳過 select_area_price）
    resp = call_api("select_ticket_count", {"count": TICKET_COUNT})
    time.sleep(2)
    if not resp or resp.get('status')!= 'success':
        print(f"❌ 選擇票數失敗: {resp.get('message') if resp else '無回應'}")
        return {'status': 'error', 'message': '選擇票數失敗'}
    # 6. 辨識驗證碼
    resp = call_api("solve_captcha")
    time.sleep(2)
    # 不管驗證碼成功或失敗都繼續
    # 7. 勾選同意條款
    resp = call_api("agree_terms")
    time.sleep(1)
    if not resp or resp.get('status') != 'success':
        print(f"❌ 勾選同意條款失敗: {resp.get('message') if resp else '無回應'}")
        return {'status': 'error', 'message': '勾選同意條款失敗'}
    # 8. 點擊確認張數
    resp = call_api("confirm_ticket")
    if not resp or resp.get('status') != 'success':
        print(f"❌ 點擊確認張數失敗: {resp.get('message') if resp else '無回應'}")
        return {'status': 'error', 'message': '點擊確認張數失敗'}
    print('🎉 全部流程執行完畢，請於瀏覽器確認結帳頁面！')
    return {"status": "success", "message": "全部流程執行完畢，請於瀏覽器確認結帳頁面！"}

# ====== 主流程 ======
def main():
    run_auto_ticket(EVENT_URL, ARTIST_KEYWORD, AREA_KEYWORDS, PRICE_KEYWORDS, TICKET_COUNT)

if __name__ == "__main__":
    main()

