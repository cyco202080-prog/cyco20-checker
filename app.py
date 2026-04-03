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
st.set_page_config(page_title="애드컴퍼니 팩트체커", page_icon="🚀", layout="centered")

st.title("📊 애드컴퍼니 10초 팩트체크")
st.markdown("현장에서 상위 10위 평균과 우리 병원 순위(100위 컷)를 스캔합니다.")

# 입력창
kw = st.text_input("🔎 검색어 (예: 평택고덕치과)")
hp = st.text_input("🏥 우리 병원명 (예: 고덕키즈앤탑치과의원)")

if st.button("🚀 순위 & 평균 스캔 시작"):
    if not kw or not hp:
        st.warning("키워드와 병원명을 모두 입력해주세요!")
    else:
        # 💡 안내 문구 수정 (해외 서버 로딩 시간 안내)
        with st.spinner("네이버 지도 정밀 스캔 중... (서버 상태에 따라 최대 20초 소요)"):
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--lang=ko_KR") # 한국어 세팅 강제
            
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
                driver.get(f"https://map.naver.com/p/search/{kw}")
                
                # 💡 대기 시간 15초로 넉넉하게 연장
                wait = WebDriverWait(driver, 15)
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "searchIframe")))
                
                # 💡 핵심: 프레임에 들어간 후 리스트가 다 그려질 때까지 무조건 3초 강제 대기
                time.sleep(3) 
                
                top10_v_reviews, top10_b_reviews = [], []
                our_rank = "100위권 밖 (마케팅 시급!)"
                global_rank = 0
                found_target = False
                processed_names = set() 
                
                target_parts = [p.replace(" ", "") for p in hp.split()]
                
                for page in range(1, 5): 
                    if found_target or global_rank >= 100: break
                    
                    try:
                        # 💡 리스트를 못 찾으면 조용히 0건 처리하지 않고 에러를 발생시킴
                        scroll_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#_pcmap_list_scroll_container")))
                    except Exception as e: 
                        if page == 1:
                            st.error("네이버 지도가 늦게 열려 리스트를 찾지 못했습니다. 다시 한 번 '스캔 시작'을 눌러주세요!")
                        break

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
                                clean_name = name_text.replace(" ", "")
                                
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
                                    
                                if all(part in clean_name for part in target_parts):
                                    our_rank = f"{global_rank}위"
                                    found_target = True
                                    break
                            except: pass
                        
                        # 💡 스크롤 내리는 시간도 조금 더 넉넉하게 확보 (0.8초)
                        driver.execute_script("arguments[0].scrollBy(0, 1200);", scroll_box)
                        time.sleep(0.8) 
                        
                    if not found_target and global_rank < 100:
                        try:
                            next_btn = driver.find_element(By.XPATH, f"//a[text()='{page + 1}']")
                            driver.execute_script("arguments[0].click();", next_btn)
                            # 💡 다음 페이지 넘어갈 때도 충분히 대기
                            time.sleep(2.5) 
                        except: break

                # 💡 안전장치: 스캔을 아예 못했을 경우 방어
                if global_rank == 0:
                    st.warning("스캔에 실패했습니다. (원인: 네이버 로딩 지연 또는 검색 결과 없음)")
                else:
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
