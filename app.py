# app.py (최종 수정본 - 깃허브에 그대로 복사해서 붙여넣으세요)
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
CORS(app)

def get_naver_rank(kw, hp):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    # 💡 Render에 설치된 크롬 경로를 강제로 지정합니다
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(f"https://map.naver.com/p/search/{kw}")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "searchIframe")))
        
        top10_v_reviews, top10_b_reviews = [], []
        our_rank = 0
        global_rank = 0
        found_target = False
        processed_names = set()
        target_parts = [p.replace(" ", "") for p in hp.split()]
        
        # 스캔 로직
        for page in range(1, 5):
            if found_target or global_rank >= 100: break
            try:
                scroll_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#_pcmap_list_scroll_container")))
            except: break

            for step in range(12):
                if found_target or global_rank >= 100: break
                curr_items = driver.find_elements(By.CSS_SELECTOR, "li")
                for item in curr_items:
                    if found_target or global_rank >= 100: break
                    try:
                        item_text = item.text
                        if not item_text or "광고" in item_text: continue
                        name_el = item.find_element(By.CSS_SELECTOR, ".place_bluelink")
                        name_text = name_el.text.split('\n')[0].strip()
                        if name_text in processed_names: continue
                        processed_names.add(name_text)
                        global_rank += 1
                        
                        v_m = re.search(r'(?:방문자리뷰|영수증리뷰)([0-9,\+]+)', item_text.replace(" ", ""))
                        b_m = re.search(r'블로그리뷰([0-9,\+]+)', item_text.replace(" ", ""))
                        v_cnt = int(v_m.group(1).replace(",", "").replace("+", "")) if v_m else 0
                        b_cnt = int(b_m.group(1).replace(",", "").replace("+", "")) if b_m else 0
                        
                        if global_rank <= 10:
                            top10_v_reviews.append(v_cnt)
                            top10_b_reviews.append(b_cnt)
                            
                        clean_name = name_text.replace(" ", "")
                        if all(part in clean_name for part in target_parts):
                            our_rank = global_rank
                            found_target = True
                            break
                    except: pass
                driver.execute_script("arguments[0].scrollBy(0, 1200);", scroll_box)
                time.sleep(0.8)
            
            if not found_target and global_rank < 100:
                try:
                    next_btn = driver.find_element(By.XPATH, f"//a[text()='{page + 1}']")
                    driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(2.5)
                except: break

        avg_v = int(sum(top10_v_reviews) / len(top10_v_reviews)) if top10_v_reviews else 0
        avg_b = int(sum(top10_b_reviews) / len(top10_b_reviews)) if top10_b_reviews else 0
        
        return {"status": "success", "our_rank": our_rank, "avg_receipt": avg_v, "avg_blog": avg_b}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if 'driver' in locals(): driver.quit()

@app.route('/check_rank', methods=['GET'])
def check_rank():
    keyword = request.args.get('kw')
    hospital = request.args.get('hp')
    if not keyword or not hospital:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400
    return jsonify(get_naver_rank(keyword, hospital))

if __name__ == '__main__':
    # 💡 Render 전용 포트 설정 (이게 없으면 500 에러 납니다)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
