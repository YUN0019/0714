from flask import Flask, request, jsonify
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import logging
import threading
import time
import os
from functools import wraps
import io
from PIL import Image, ImageOps
import pytesseract

# ========== 設定 pytesseract 路徑（請依你本機安裝路徑調整） ==========
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Alexander\tesseract\tesseract.exe'

# ========== 初始化 Flask 應用 ==========
app = Flask(__name__)

# ========== log 輸出到檔案 ==========
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger()
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    logger.addHandler(file_handler)
else:
    for h in logger.handlers:
        logger.removeHandler(h)
    logger.addHandler(file_handler)

# ========== API TOKEN 驗證 ==========
API_TOKEN = os.environ.get('API_TOKEN', 'my_secret_token')
def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-TOKEN')
        if token != API_TOKEN:
            return jsonify({'status': 'error', 'message': 'API token 驗證失敗'}), 401
        return f(*args, **kwargs)
    return decorated

# ========== 全域 Selenium driver ==========
driver = None

def init_browser():
    global driver
    options = uc.ChromeOptions()
    # options.add_argument('--headless')  # 測試時建議先不要 headless
    options.add_argument('--disable-gpu')
    # 可選：沿用本地 Chrome 使用者資料夾（已登入 Google/Facebook 狀態）
    # options.add_argument('--user-data-dir=C:/Users/你的帳號/AppData/Local/Google/Chrome/User Data')
    # options.add_argument('--profile-directory=Default')
    driver = uc.Chrome(options=options)
    logging.info('瀏覽器初始化完成 (undetected-chromedriver)')

# ========== API: 開啟任意網址（如登入頁、活動頁） ==========
@app.route('/open_url', methods=['POST'])
@require_token
def open_url():
    global driver
    if driver is None:
        return jsonify({'status': 'error', 'message': 'Selenium driver 尚未初始化'}), 500
    req_json = request.get_json() or {}
    url = req_json.get('url')
    try:
        driver.get(url)
        logging.info(f'已開啟網址: {url}')
        return jsonify({'status': 'success', 'message': f'已開啟網址: {url}'})
    except Exception as e:
        logging.exception(f'開啟網址失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'開啟網址失敗: {str(e)}'}), 500

# ========== API: 儲存/載入 cookie ==========
@app.route('/save_cookie', methods=['POST'])
@require_token
def save_cookie():
    global driver
    if driver is None:
        return jsonify({'status': 'error', 'message': 'Selenium driver 尚未初始化'}), 500
    try:
        cookies = driver.get_cookies()
        with open('cookies.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(cookies, f, ensure_ascii=False)
        logging.info('Cookie 已儲存')
        return jsonify({'status': 'success', 'message': 'Cookie 已儲存'})
    except Exception as e:
        logging.exception(f'Cookie 儲存失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'Cookie 儲存失敗: {str(e)}'}), 500

@app.route('/load_cookie', methods=['POST'])
@require_token
def load_cookie():
    global driver
    if driver is None:
        return jsonify({'status': 'error', 'message': 'Selenium driver 尚未初始化'}), 500
    try:
        _ = driver.current_url
    except Exception:
        return jsonify({'status': 'error', 'message': '請先用 /open_url 開啟一個網頁再載入 cookie'}), 400
    try:
        import json
        with open('cookies.json', 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
        logging.info('Cookie 已載入')
        return jsonify({'status': 'success', 'message': 'Cookie 已載入'})
    except Exception as e:
        logging.exception(f'Cookie 載入失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'Cookie 載入失敗: {str(e)}'}), 500

# ========== API: 自動刷新與開賣偵測 ==========
@app.route('/refresh', methods=['POST'])
@require_token
def refresh():
    global driver
    if driver is None:
        return jsonify({'status': 'error', 'message': 'Selenium driver 尚未初始化'}), 500
    req_json = request.get_json() or {}
    url = req_json.get('url')
    interval = req_json.get('interval', 5)
    trigger_text = req_json.get('trigger_text', '立即訂票')
    try:
        driver.get(url)
        while True:
            page_source = driver.page_source
            if trigger_text in page_source:
                logging.info('偵測到開賣！')
                break
            logging.info(f'尚未開賣，等待 {interval} 秒後刷新...')
            time.sleep(interval)
            driver.refresh()
        return jsonify({'status': 'success', 'message': '開賣偵測完成'})
    except Exception as e:
        logging.exception(f'刷新失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'刷新失敗: {str(e)}'}), 500

# ========== API: 自動選票與送單（拓元） ==========
@app.route('/select_ticket', methods=['POST'])
@require_token
def select_ticket():
    global driver
    if driver is None:
        return jsonify({'status': 'error', 'message': 'Selenium driver 尚未初始化'}), 500
    data = request.get_json() or {}
    try:
        ticket_type_selector = data.get('ticket_type_selector', 'select.ticket-select')
        quantity_selector = data.get('quantity_selector', 'input.form-control')
        submit_selector = data.get('submit_selector', 'button.next')
        ticket_type_value = data.get('ticket_type_value')
        quantity = data.get('quantity', 1)
        ticket_dropdown = driver.find_element(By.CSS_SELECTOR, ticket_type_selector)
        from selenium.webdriver.support.ui import Select
        select = Select(ticket_dropdown)
        if ticket_type_value:
            select.select_by_value(ticket_type_value)
        else:
            select.select_by_index(1)
        quantity_input = driver.find_element(By.CSS_SELECTOR, quantity_selector)
        quantity_input.clear()
        quantity_input.send_keys(str(quantity))
        submit_button = driver.find_element(By.CSS_SELECTOR, submit_selector)
        submit_button.click()
        logging.info('送出訂單成功（拓元選票）')
        return jsonify({'status': 'success', 'message': '選票與送單成功（拓元）'})
    except Exception as e:
        logging.exception(f'選票或送單失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'操作失敗: {str(e)}'}), 500

# ========== API: 自動選座（拓元） ==========
@app.route('/select_seat', methods=['POST'])
@require_token
def select_seat():
    global driver
    if driver is None:
        return jsonify({'status': 'error', 'message': 'Selenium driver 尚未初始化'}), 500
    data = request.get_json() or {}
    try:
        seat_selector = data.get('seat_selector', '.area-seat:not(.sold)')
        confirm_selector = data.get('confirm_selector', 'button.confirm-seat')
        seat_elem = driver.find_element(By.CSS_SELECTOR, seat_selector)
        seat_elem.click()
        time.sleep(1)
        confirm_elem = driver.find_element(By.CSS_SELECTOR, confirm_selector)
        confirm_elem.click()
        logging.info('選座成功（拓元）')
        return jsonify({'status': 'success', 'message': '選座成功（拓元）'})
    except Exception as e:
        logging.exception(f'選座失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'選座失敗: {str(e)}'}), 500

# ========== API: 驗證碼辨識 ==========
@app.route('/captcha', methods=['POST'])
@require_token
def captcha():
    if driver is None:
        return jsonify({'status': 'error', 'message': 'Selenium driver 尚未初始化'}), 500
    if 'captcha' not in request.files:
        return jsonify({'status': 'error', 'message': '未提供圖片檔案'}), 400
    file = request.files['captcha']
    try:
        image = Image.open(io.BytesIO(file.read()))
        image = ImageOps.grayscale(image)
        # 改用正確的二值化方式
        threshold = 128
        image = image.point(lambda x: 255 if x > threshold else 0, '1')
        text = pytesseract.image_to_string(image)
        cleaned_text = text.strip()
        logging.info(f'驗證碼辨識結果: {cleaned_text}')
        return jsonify({'status': 'success', 'captcha_text': cleaned_text})
    except Exception as e:
        logging.exception(f'OCR 失敗: {str(e)}')
        return jsonify({'status': 'error', 'message': f'OCR 失敗: {str(e)}'}), 500

# ========== 啟動 Flask 與 Selenium ==========
if __name__ == '__main__':
    threading.Thread(target=init_browser).start()
    app.run(host='0.0.0.0', port=5000)
