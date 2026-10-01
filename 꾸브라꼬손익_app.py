import streamlit as st
import pandas as pd

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(page_title="꾸브라꼬 가맹점 손익 계산기", layout="wide")

st.title("🍗 꾸브라꼬 가맹점 실시간 손익 시뮬레이터")
st.markdown("엑셀 파일을 드래그하여 업로드하면, 매장별 데이터를 불러와 실시간으로 수정 및 손익 계산을 해볼 수 있습니다.")

# ==========================================
# 2. 파일 업로드 로직
# ==========================================
uploaded_file = st.file_uploader("📂 '가맹점_손익시트.xlsx' 파일을 여기에 드래그하거나 클릭하여 업로드하세요.", type=["xlsx"])

@st.cache_data
def load_excel_data(file):
    try:
        df = pd.read_excel(file, sheet_name="손익 시트", header=3)
        df_clean = df.dropna(how="all").dropna(subset=["매장명"]).copy()
        
        num_cols = df_clean.columns.drop(["No.", "매장명"])
        for c in num_cols:
            df_clean[c] = pd.to_numeric(df_clean[c], errors="coerce").fillna(0)
        return df_clean
    except Exception as e:
        st.error(f"엑셀 파일을 읽는 중 오류 발생: {e}")
        return None

if uploaded_file is not None:
    df = load_excel_data(uploaded_file)
    
    if df is not None and not df.empty:
        store_list = df["매장명"].astype(str).tolist()

        # ==========================================
        # 3. 매장 선택 및 데이터 연동 (변수 초기화)
        # ==========================================
        st.divider()
        selected_store = st.selectbox("🏪 분석할 매장 선택", options=store_list)
        store_data = df[df["매장명"] == selected_store].iloc[0]

        # 엑셀 데이터 추출 (세션 스테이트 없이 즉시 반영)
        월매출_val = int(store_data.get("월 매출", 0))
        배민_val = int(store_data.get("배민\n(입금기준)", 0))
        요기요_val = int(store_data.get("요기요\n(입금기준)", 0))
        쿠팡이츠_val = int(store_data.get("쿠팡이츠\n(입금기준)", 0))
        땡겨요_val = int(store_data.get("땡겨요\n(입금기준)", 0))
        위메프오_val = int(store_data.get("위메프오\n(입금기준)", 0))
        포스매출_val = int(store_data.get("포스매출", 0))
        기타매출_val = int(store_data.get("기타\n(먹깨비, 울산페달, 양산배달)", 0))
        
        물류대_val = int(store_data.get("물류대", 0))
        기름_val = int(store_data.get("기름", 0))
        음료_val = int(store_data.get("음료", 0))
        주류_val = int(store_data.get("주류", 0))

        인건비_val = int(store_data.get("인건비", 0))
        월세_val = int(store_data.get("월세", 0))
        공과금_val = int(store_data.get("공과금", 0))
        퀵비_val = int(store_data.get("퀵비", 0))
        포스이용료_val = int(store_data.get("포스이용료", 0))
        기타잡비_val = int(store_data.get("기타 잡비\n(보험·인터넷·정수기 등)", 0))

        # ==========================================
        # 4. 입력 UI (레이아웃 하단 배치 위해 sidebar 또는 아래쪽에 배치)
        # ==========================================
        # 먼저 변수들을 받아 계산을 해야 하므로, 레이아웃을 컨테이너로 분리합니다.
        results_container = st.container()
        st.divider()
        st.markdown("### 📝 세부 데이터 입력 및 수정 (기본 정보)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🔹 매출 및 플랫폼 입금")
            월매출 = st.number_input("월 매출 (총매출액)", value=월매출_val, step=100000)
            배민 = st.number_input("배민 (입금기준)", value=배민_val, step=10000)
            요기요 = st.number_input("요기요 (입금기준)", value=요기요_val, step=10000)
            쿠팡이츠 = st.number_input("쿠팡이츠 (입금기준)", value=쿠팡이츠_val, step=10000)
            땡겨요 = st.number_input("땡겨요 (입금기준)", value=땡겨요_val, step=10000)
            위메프오 = st.number_input("위메프오 (입금기준)", value=위메프오_val, step=10000)
            포스매출 = st.number_input("포스매출", value=포스매출_val, step=10000)
            기타매출 = st.number_input("기타 (먹깨비 등)", value=기타매출_val, step=10000)

        with col2:
            st.markdown("#### 🔹 물류 비용")
            물류대 = st.number_input("물류대", value=물류대_val, step=100000)
            기름 = st.number_input("기름", value=기름_val, step=10000)
            음료 = st.number_input("음료", value=음료_val, step=10000)
            주류 = st.number_input("주류", value=주류_val, step=10000)

        with col3:
            st.markdown("#### 🔹 운영 비용")
            인건비 = st.number_input("인건비", value=인건비_val, step=100000)
            월세 = st.number_input("월세", value=월세_val, step=10000)
            공과금 = st.number_input("공과금", value=공과금_val, step=10000)
            퀵비 = st.number_input("퀵비", value=퀵비_val, step=10000)
            포스이용료 = st.number_input("포스이용료", value=포스이용료_val, step=1000)
            기타잡비 = st.number_input("기타 경비 (보험, 인터넷 등)", value=기타잡비_val, step=10000)

        # ==========================================
        # 5. 실시간 손익 계산 (계산 로직)
        # ==========================================
        입금합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타매출
        
        # 물류 합계 (물류대 + 기름 + 음료 + 주류)
        물류합계 = 물류대 + 기름 + 음료 + 주류
        
        # 운영 합계 (인건비 + 월세 + 공과금 + 퀵비 + 포스이용료 + 기타잡비)
        운영합계 = 인건비 + 월세 + 공과금 + 퀵비 + 포스이용료 + 기타잡비
        
        # 최종 수익 계산: 입금합계 - (물류합계 + 운영합계)
        최종금액 = 입금합계 - 물류합계 - 운영합계

        # 퍼센트 계산 (0으로 나누기 방지)
        # 퍼센트의 기준: 월매출을 기준으로 하는 것이 일반적이므로 월매출 기준으로 작성
        물류비율 = (물류합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        운영비율 = (운영합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        입금비율 = (입금합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        
        # 최종 수익률은 '입금 합계' 대비 수익인지 '월 매출' 대비 수익인지에 따라 다름. 
        # 엑셀 원본 로직에 따라 입금합계 대비 수익률 계산
        수익률 = (최종금액 / 입금합계 * 100) if 입금합계 > 0 else 0.0
        수익률_매출대비 = (최종금액 / 월매출 * 100) if 월매출 > 0 else 0.0

        # ==========================================
        # 6. 상단 결과 요약 화면 렌더링
        # ==========================================
        with results_container:
            st.subheader(f"📊 [{selected_store}] 실시간 시뮬레이션 결과")
            
            # 5개의 주요 결과를 나란히 배치 (매출 -> 입금 -> 물대(물류) -> 운영비 -> 수익)
            m1, m2, m3, m4, m5 = st.columns(5)
            
            m1.metric(label="1️⃣ 월 매출액", value=f"{월매출:,.0f} 원", delta="100.00 % (기준)", delta_color="off")
            m2.metric(label="2️⃣ 입금 합계", value=f"{입금합계:,.0f} 원", delta=f"매출대비: {입금비율:.2f}%", delta_color="normal")
            m3.metric(label="3️⃣ 물류 합계", value=f"{물류합계:,.0f} 원", delta=f"매출대비: {물류비율:.2f}%", delta_color="inverse")
            m4.metric(label="4️⃣ 운영비 합계", value=f"{운영합계:,.0f} 원", delta=f"매출대비: {운영비율:.2f}%", delta_color="inverse")
            m5.metric(label="💰 최종 순수익", value=f"{최종금액:,.0f} 원", delta=f"수익률(입금대비): {수익률:.2f}%")
            
            st.caption(f"※ (참고) 월 매출 대비 최종 순수익률은 **{수익률_매출대비:.2f}%** 입니다.")
            
else:
    st.info("👆 위 영역에 엑셀 파일을 업로드(드래그) 해주세요.")