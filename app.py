import streamlit as st
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# 모바일 화면 디자인 세팅
st.set_page_config(page_title="애드컴퍼니 팩트체크", page_icon="🚀", layout="centered")

st.title("📊 애드컴퍼니 10초 팩트체크")
st.markdown("현장에서 상위 10위 평균과 우리 병원 순위(100위 컷)를 스캔합니다.")

# 입력창
kw = st.text_input("🔎 검색어 (예: 강남역 치과)")
hp = st.text_input("🏥 우리 병원명 (예: 미유치과의원)")

# 버튼을 누르면 실행
if st.button("🚀 순위 & 평균 스캔 시작"):
    if not kw or not hp:
        st.warning("키워드와 병원명을 모두 입력해주세요!")
    else:
        with st.spinner("네이버 지도 고속 스캔 중... (약 10~15초 소요)"):
            
            # 서버용 숨김 브라우저 세팅
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
                driver.get(f"https://map.naver.com/p/search/{kw}")
                time.sleep(3.5)
                driver.switch_to.frame("searchIframe")
                
                top10_v_reviews, top10_b_reviews = [], []
                our_rank = "100위권 밖 (마케팅 시급!)"
                global_rank, found_target = 0, False
                target_parts = [p.replace(" ", "") for p in hp.split()]
                
                # 최대 3페이지(100위~150위) 고속 스캔
                for page in range(1, 4):
                    if found_target or global_rank >= 100: break
                    
                    scroll_box = driver.find_element(By.CSS_SELECTOR, "#_pcmap_list_scroll_container")
                    for step in range(10): 
                        if found_target or global_rank >= 100: break
                        
                        curr_items = driver.find_elements(By.CSS_SELECTOR, "li")
                        for item in curr_items:
                            if found_target or global_rank >= 100: break
                            try:
                                item_text = item.text
                                if not item_text or "광고" in item_text: continue
                                
                                name_text = item.find_element(By.CSS_SELECTOR, ".place_bluelink").text.split('\n')[0]
                                clean_name = name_text.replace(" ", "")
                                global_rank += 1
                                
                                v_m = re.search(r'(?:방문자리뷰|영수증리뷰)([0-9,\+]+)', item_text.replace(" ", ""))
                                b_m = re.search(r'블로그리뷰([0-9,\+]+)', item_text.replace(" ", ""))
                                v_cnt = int(v_m.group(1).replace(",", "").replace("+", "")) if v_m else 0
                                b_cnt = int(b_m.group(1).replace(",", "").replace("+", "")) if b_m else 0
                                
                                if global_rank <= 10:
                                    top10_v_reviews.append(v_cnt)
                                    top10_b_reviews.append(b_cnt)
                                    
                                if all(part in clean_name for part in target_parts):
                                    our_rank = f"{global_rank}위"
                                    found_target = True
                                    break
                            except: pass
                        driver.execute_script("arguments[0].scrollBy(0, 800);", scroll_box)
                        time.sleep(0.3)
                        
                    if not found_target and global_rank < 100:
                        try:
                            next_btn = driver.find_element(By.XPATH, f"//a[text()='{page + 1}']")
                            driver.execute_script("arguments[0].click();", next_btn); time.sleep(1.5)
                        except: break

                # 결과 출력
                avg_v = int(sum(top10_v_reviews) / len(top10_v_reviews)) if top10_v_reviews else 0
                avg_b = int(sum(top10_b_reviews) / len(top10_b_reviews)) if top10_b_reviews else 0

                st.success("스캔 완료!")
                st.markdown(f"### 🎯 우리 병원 순위: <span style='color:red;'>{our_rank}</span>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("### 📊 상위 경쟁사(1~10위) 평균")
                st.write(f"✔️ 평균 영수증 리뷰: **{avg_v}건**")
                st.write(f"✔️ 평균 블로그 리뷰: **{avg_b}건**")

            except Exception as e:
                st.error(f"에러가 발생했습니다: {e}")
            finally:
                if 'driver' in locals():
                    driver.quit()