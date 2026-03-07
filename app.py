import streamlit as st
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# 모바일 화면 디자인 세팅
st.set_page_config(page_title="애드컴퍼니 제공 플레이스 순위 및 리뷰체크v3.2", page_icon="🚀", layout="centered")

st.title("📊 애드컴퍼니 제공 플레이스 순위 및 리뷰체크v3.2")
st.markdown("현장에서 상위 10위 리뷰 평균수 와 플레이스 순위(100위 컷)를 스캔합니다.")

# 입력창
kw = st.text_input("🔎 검색어 (예: 분당 피부과 )")
hp = st.text_input("🏥 우리 병원명 (예: 아비쥬의원 분당)")

if st.button("🚀 순위 & 평균 스캔 시작"):
    if not kw or not hp:
        st.warning("키워드와 병원명을 모두 입력해주세요!")
    else:
        with st.spinner("네이버 플레이스 스캔 중..."):
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
            options.add_argument("--window-size=1920,1080")
            
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
                driver.get(f"https://map.naver.com/p/search/{kw}")
                
                wait = WebDriverWait(driver, 10)
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "searchIframe")))
                
                top10_v_reviews, top10_b_reviews = [], []
                our_rank = "100위권 밖 (마케팅 시급!)"
                global_rank = 0
                found_target = False
                processed_names = set() # 💡 중복 제거용 필터
                
                target_parts = [p.replace(" ", "") for p in hp.split()]
                
                # 100위 컷 고속 스캔
                for page in range(1, 5): # 최대 4페이지까지 확장
                    if found_target or global_rank >= 100: break
                    
                    try:
                        scroll_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#_pcmap_list_scroll_container")))
                    except: break

                    for step in range(12): 
                        if found_target or global_rank >= 100: break
                        
                        # 모든 리스트 항목을 가져옴
                        curr_items = driver.find_elements(By.CSS_SELECTOR, "li")
                        for item in curr_items:
                            if found_target or global_rank >= 100: break
                            try:
                                item_text = item.text
                                if not item_text or "광고" in item_text: continue
                                
                                # 병원명 추출
                                name_el = item.find_element(By.CSS_SELECTOR, ".place_bluelink")
                                name_text = name_el.text.split('\n')[0].strip()
                                clean_name = name_text.replace(" ", "")
                                
                                # 💡 [중심 로직] 이미 세어본 병원이라면 패스! (중복 방지)
                                if name_text in processed_names: continue
                                
                                # 처음 보는 병원일 때만 카운트 증가
                                processed_names.add(name_text)
                                global_rank += 1
                                
                                # 리뷰 데이터 수집 (상위 10위만)
                                v_m = re.search(r'(?:방문자리뷰|영수증리뷰)([0-9,\+]+)', item_text.replace(" ", ""))
                                b_m = re.search(r'블로그리뷰([0-9,\+]+)', item_text.replace(" ", ""))
                                v_cnt = int(v_m.group(1).replace(",", "").replace("+", "")) if v_m else 0
                                b_cnt = int(b_m.group(1).replace(",", "").replace("+", "")) if b_m else 0
                                
                                if global_rank <= 10:
                                    top10_v_reviews.append(v_cnt)
                                    top10_b_reviews.append(b_cnt)
                                    
                                # 우리 병원 매칭 확인
                                if all(part in clean_name for part in target_parts):
                                    our_rank = f"{global_rank}위"
                                    found_target = True
                                    break
                            except: pass
                        
                        # 스크롤 내려서 다음 목록 불러오기
                        driver.execute_script("arguments[0].scrollBy(0, 1200);", scroll_box)
                        time.sleep(0.6)
                        
                    # 다음 페이지 버튼 클릭
                    if not found_target and global_rank < 100:
                        try:
                            next_btn = driver.find_element(By.XPATH, f"//a[text()='{page + 1}']")
                            driver.execute_script("arguments[0].click();", next_btn)
                            time.sleep(2.0)
                        except: break

                # 결과 출력
                avg_v = int(sum(top10_v_reviews) / len(top10_v_reviews)) if top10_v_reviews else 0
                avg_b = int(sum(top10_b_reviews) / len(top10_b_reviews)) if top10_b_reviews else 0

                st.success("스캔 완료!")
                st.markdown(f"### 🎯 우리 병원 순위: <span style='color:red;'>{our_rank}</span>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("### 📊 상위 경쟁사(1~10위) 평균")
                st.write(f"✔️ 평균 영수증 리뷰: **{avg_v:,}건**")
                st.write(f"✔️ 평균 블로그 리뷰: **{avg_b:,}건**")

            except Exception as e:
                st.error(f"데이터를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            finally:
                if 'driver' in locals():
                    driver.quit()

