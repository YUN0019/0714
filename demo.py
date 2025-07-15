import threading
import json
import logging
import time
import undetected_chromedriver as uc
from flask import Flask, request, jsonify
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageOps, ImageFilter
import pytesseract
from collections import Counter
from selenium.common.exceptions import WebDriverException
import os

# ========== 設定 pytesseract 路徑 ==========
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Alexander\tesseract\tesseract.exe'  # 請依實際安裝路徑調整

API_TOKEN = "my_secret_token"
driver = None
app = Flask(__name__)

def get_driver():
    global driver
    # 強制初始化直到 driver 不為 None
    retry = 0
    while driver is None and retry < 3:
        init_browser()
        retry += 1
    try:
        _ = driver.title
    except Exception:
        init_browser()
    if driver is None:
        raise RuntimeError('Selenium driver 初始化失敗')
    return driver

# ========== log 設定 ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def require_token(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-TOKEN')
        if token != API_TOKEN:
            return jsonify({'status': 'error', 'message': 'API token 驗證失敗'}), 401
        return f(*args, **kwargs)
    return decorated

def init_browser():
    global driver
    try:
        if driver is not None:
            driver.quit()
    except Exception:
        pass
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    logging.info('瀏覽器初始化完成')

def require_driver_ready(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        d = get_driver()
        return f(*args, **kwargs)
    return decorated

def save_debug_screenshot(step_name, attempt):
    d = get_driver()
    if not os.path.exists('debug_screenshots'):
        os.makedirs('debug_screenshots')
    path = f"debug_screenshots/{step_name}_{attempt}.png"
    d.save_screenshot(path)
    return path

# search_event
@app.route('/search_event', methods=['POST'])
@require_token
@require_driver_ready
def search_event():
    d = get_driver()
    data = request.get_json() or {}
    keyword = data.get('keyword') or ""
    for attempt in range(3):
        try:
            d.get("https://tixcraft.com/")
            time.sleep(2)
            search_box = WebDriverWait(d, 10).until(
                EC.element_to_be_clickable((By.ID, "txt_search"))
            )
            search_box.clear()
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)
            event_links = d.find_elements(By.CSS_SELECTOR, ".event-list a")
            if not event_links:
                raise Exception(f'找不到關鍵字「{keyword}」的活動')
            return jsonify({'status': 'success', 'event_count': len(event_links)})
        except Exception as e:
            path = save_debug_screenshot('search_event', attempt)
            logging.exception(f'搜尋活動失敗: {str(e)}')
            if attempt == 2:
                return jsonify({'status': 'error', 'message': f'搜尋活動失敗: {str(e)}', 'screenshot': path, 'title': d.title, 'url': d.current_url}), 500
            time.sleep(1)
    return jsonify({'status': 'error', 'message': '搜尋活動失敗'})

# enter_event_detail
@app.route('/enter_event_detail', methods=['POST'])
@require_token
@require_driver_ready
def enter_event_detail():
    d = get_driver()
    for attempt in range(3):
        try:
            event_link = WebDriverWait(d, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.thumbnails"))
            )
            event_link.click()
            time.sleep(2)
            if not d.find_elements(By.CSS_SELECTOR, "button.btn.btn-primary.text-bold.m-0"):
                raise Exception('未進入活動詳情頁')
            logging.info('已點擊活動卡片 a.thumbnails')
            return jsonify({'status': 'success'})
        except Exception as e:
            path = save_debug_screenshot('enter_event_detail', attempt)
            logging.exception(f'點擊活動頁失敗: {str(e)}')
            if attempt == 2:
                return jsonify({'status': 'error', 'message': f'點擊活動頁失敗: {str(e)}', 'screenshot': path, 'title': d.title, 'url': d.current_url}), 500
            time.sleep(1)

@app.route('/click_buy_now', methods=['POST'])
@require_token
@require_driver_ready
def click_buy_now():
    d = get_driver()
    for attempt in range(3):
        try:
            old_tabs = d.window_handles
            try:
                btn = d.find_element(By.XPATH, "//button[contains(text(),'立即訂票') or contains(text(),'立即購票')]")
            except:
                btn = d.find_element(By.CSS_SELECTOR, "li.buy a, a[href^='/activity/game/'][target='_new']")
            d.execute_script("arguments[0].click();", btn)
            time.sleep(2)
            new_tabs = d.window_handles
            if len(new_tabs) > len(old_tabs):
                d.switch_to.window(new_tabs[-1])
            btn2 = WebDriverWait(d, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.text-bold.m-0"))
            )
            d.execute_script("arguments[0].click();", btn2)
            time.sleep(2)
            if not d.find_elements(By.CSS_SELECTOR, ".area-list a[id]"):
                raise Exception('未進入選位置頁')
            return jsonify({'status': 'success'})
        except Exception as e:
            path = save_debug_screenshot('click_buy_now', attempt)
            logging.exception(f'點擊立即購票失敗: {str(e)}')
            if attempt == 2:
                return jsonify({'status': 'error', 'message': f'點擊立即購票失敗: {str(e)}', 'screenshot': path, 'title': d.title, 'url': d.current_url}), 500
            time.sleep(1)

@app.route('/select_area_price', methods=['POST'])
@require_token
@require_driver_ready
def select_area_price():
    d = get_driver()
    data = request.get_json() or {}
    area_keywords = data.get('area_keywords', ["A區"])
    price_keywords = data.get('price_keywords', ["5400"])
    for attempt in range(3):
        try:
            area_links = d.find_elements(By.CSS_SELECTOR, ".area-list a")
            found = False
            for a in area_links:
                text = a.text
                if any(kw in text for kw in area_keywords) and any(pk in text for pk in price_keywords):
                    d.execute_script("arguments[0].click();", a)
                    found = True
                    logging.info(f"已選擇區域/價格: {text}")
                    break
            if not found and area_links:
                d.execute_script("arguments[0].click();", area_links[0])
                logging.info(f"未找到首選，已選擇備選: {area_links[0].text}")
            WebDriverWait(d, 10).until(
                lambda d2: d2.find_elements(By.CSS_SELECTOR, "select[id^='TicketForm_ticketPrice_']")
            )
            return jsonify({'status': 'success'})
        except Exception as e:
            path = save_debug_screenshot('select_area_price', attempt)
            logging.exception(f'選擇區域/價格失敗: {str(e)}')
            if attempt == 2:
                return jsonify({'status': 'error', 'message': f'選擇區域/價格失敗: {str(e)}', 'screenshot': path, 'title': d.title, 'url': d.current_url}), 500
            time.sleep(1)

@app.route('/select_ticket_count', methods=['POST'])
@require_token
@require_driver_ready
def select_ticket_count():
    d = get_driver()
    data = request.get_json() or {}
    count = data.get('count', 1)
    for attempt in range(3):
        try:
            if not d.find_elements(By.CSS_SELECTOR, "select[id^='TicketForm_ticketPrice_']"):
                raise Exception(f'目前不在選票數頁面，當前頁面：{d.title}, {d.current_url}')
            select_elem = WebDriverWait(d, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "select[id^='TicketForm_ticketPrice_']"))
            )
            d.execute_script("arguments[0].click();", select_elem)
            try:
                select = Select(select_elem)
                select.select_by_value(str(count))
            except Exception:
                option_elem = WebDriverWait(d, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"select[id^='TicketForm_ticketPrice_'] option[value='{count}']"))
                )
                d.execute_script("arguments[0].click();", option_elem)
            logging.info(f"已選擇票數: {count}")
            return jsonify({'status': 'success', 'count': count})
        except Exception as e:
            path = save_debug_screenshot('select_ticket_count', attempt)
            logging.exception(f'選擇票數失敗: {str(e)}')
            if attempt == 2:
                return jsonify({'status': 'error', 'message': f'選擇票數失敗: {str(e)}', 'screenshot': path, 'title': d.title, 'url': d.current_url}), 500
            time.sleep(1)

@app.route('/solve_captcha', methods=['POST'])
@require_token
@require_driver_ready
def solve_captcha():
    d = get_driver()
    def preprocess_and_ocr(img_path):
        img = Image.open(img_path)
        results = []
        img1 = img.convert('L')
        img2 = ImageOps.invert(img1)
        # PIL 10+ 用 Image.Resampling.LANCZOS
        try:
            RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
        except AttributeError:
            RESAMPLE_LANCZOS = Image.LANCZOS
        img3 = img2.point(lambda x: 0 if isinstance(x, int) and x < 140 else 255, '1')
        img4 = img3.resize((img3.width * 2, img3.height * 2), RESAMPLE_LANCZOS)
        img5 = img4.filter(ImageFilter.SHARPEN)
        imgs = [img1, img2, img3, img4, img5]
        configs = [
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
            '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
            '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        ]
        for im in imgs:
            for cfg in configs:
                code = pytesseract.image_to_string(im, config=cfg).strip()
                code = ''.join(filter(str.isalnum, code))[:4]
                if len(code) == 4:
                    results.append(code)
        if results:
            return Counter(results).most_common(1)[0][0]
        return ""
    try:
        captcha_img = WebDriverWait(d, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img#TicketForm_verifyCode-image"))
        )
        img_path = f"captcha_0.png"
        captcha_img.screenshot(img_path)
        code = preprocess_and_ocr(img_path)
        input_box = WebDriverWait(d, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input#TicketForm_verifyCode"))
        )
        input_box.clear()
        input_box.send_keys(code)
        logging.info(f"辨識驗證碼: {code}")
        time.sleep(2)  # 等待頁面反應
        input_elems = d.find_elements(By.CSS_SELECTOR, "input#TicketForm_verifyCode")
        if not input_elems:
            return jsonify({'status': 'success', 'captcha': code})
        input_elem = input_elems[0]
        if not input_elem.is_enabled() or input_elem.get_attribute('value') != code:
            return jsonify({'status': 'success', 'captcha': code})
        # 只要 input 還在且內容還是剛剛輸入的 code，視為失敗
        return jsonify({'status': 'error', 'message': '驗證碼辨識失敗，請人工處理'})
    except Exception as e:
        path = save_debug_screenshot('solve_captcha', 0)
        logging.exception(f'驗證碼處理失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'驗證碼處理失敗: {str(e)}', 'screenshot': path, 'title': d.title, 'url': d.current_url}), 500

@app.route('/agree_terms', methods=['POST'])
@require_token
@require_driver_ready
def agree_terms():
    d = get_driver()
    for attempt in range(3):
        try:
            checkbox = WebDriverWait(d, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input#TicketForm_agree"))
            )
            if not checkbox.is_selected():
                d.execute_script("arguments[0].click();", checkbox)
            logging.info('已勾選同意條款')
            return jsonify({'status': 'success'})
        except Exception as e:
            path = save_debug_screenshot('agree_terms', attempt)
            logging.exception(f'勾選同意條款失敗: {str(e)}')
            if attempt == 2:
                return jsonify({'status': 'error', 'message': f'勾選同意條款失敗: {str(e)}', 'screenshot': path, 'title': d.title, 'url': d.current_url}), 500
            time.sleep(1)

@app.route('/confirm_ticket', methods=['POST'])
@require_token
@require_driver_ready
def confirm_ticket():
    d = get_driver()
    for attempt in range(3):
        try:
            btn = WebDriverWait(d, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.btn-green"))
            )
            d.execute_script("arguments[0].click();", btn)
            logging.info('已點擊確認張數')
            return jsonify({'status': 'success'})
        except Exception as e:
            path = save_debug_screenshot('confirm_ticket', attempt)
            logging.exception(f'點擊確認張數失敗: {str(e)}')
            if attempt == 2:
                return jsonify({'status': 'error', 'message': f'點擊確認張數失敗: {str(e)}', 'screenshot': path, 'title': d.title, 'url': d.current_url}), 500
            time.sleep(1)

@app.route('/go_checkout', methods=['POST'])
@require_token
@require_driver_ready
def go_checkout():
    d = get_driver()
    try:
        next_btn = d.find_element(By.CSS_SELECTOR, "button.next")
        next_btn.click()
        time.sleep(2)
        if "checkout" in d.current_url or "付款" in d.title:
            logging.info("已進入結帳頁")
            return jsonify({'status': 'success', 'url': d.current_url, 'title': d.title})
        else:
            return jsonify({'status': 'error', 'message': '未進入結帳頁', 'url': d.current_url, 'title': d.title}), 400
    except Exception as e:
        logging.exception(f'跳轉結帳頁失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'跳轉結帳頁失敗: {str(e)}'}), 500

@app.route('/save_cookie', methods=['POST'])
@require_token
@require_driver_ready
def save_cookie():
    d = get_driver()
    try:
        cookies = d.get_cookies()
        with open('cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False)
        logging.info('Cookie 已儲存')
        return jsonify({'status': 'success', 'message': 'Cookie 已儲存'})
    except Exception as e:
        logging.exception(f'Cookie 儲存失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'Cookie 儲存失敗: {str(e)}'}), 500

@app.route('/load_cookie', methods=['POST'])
@require_token
@require_driver_ready
def load_cookie():
    d = get_driver()
    try:
        import os
        if not os.path.exists('cookies.json'):
            return jsonify({'status': 'error', 'message': '找不到 cookies.json，請先手動登入並存 cookie'}), 404
        with open('cookies.json', 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        d.get("https://tixcraft.com/")
        d.delete_all_cookies()
        for cookie in cookies:
            cookie.pop('sameSite', None)
            if 'expiry' in cookie and cookie['expiry'] is not None:
                cookie['expiry'] = int(cookie['expiry'])
            cookie['domain'] = '.tixcraft.com'
            d.add_cookie(cookie)
        d.refresh()
        time.sleep(2)
        page = d.page_source
        if "會員" in page or "登出" in page:
            logging.info('Cookie 已載入且登入成功')
            return jsonify({'status': 'success', 'message': 'Cookie 已載入且登入成功'})
        else:
            logging.warning('Cookie 載入但未登入，請檢查 cookie 有效性')
            return jsonify({'status': 'error', 'message': 'Cookie 載入但未登入，請重新登入並存 cookie'}), 401
    except Exception as e:
        logging.exception(f'Cookie 載入失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'Cookie 載入失敗: {str(e)}'}), 500

@app.route('/goto_event_page', methods=['POST'])
@require_token
@require_driver_ready
def goto_event_page():
    d = get_driver()
    data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({'status': 'error', 'message': '缺少活動頁網址'}), 400
    try:
        d.get(url)
        time.sleep(2)
        return jsonify({'status': 'success', 'message': '已跳轉活動頁'})
    except Exception as e:
        logging.exception(f'跳轉活動頁失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'跳轉活動頁失敗: {str(e)}'}), 500

if __name__ == '__main__':
    init_browser()  # 直接主線程初始化
    app.run(host='0.0.0.0', port=5000)
