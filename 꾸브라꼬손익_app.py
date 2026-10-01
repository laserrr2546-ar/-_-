import streamlit as st
import pandas as pd

# ==========================================
# 1. 페이지 설정 및 꾸브라꼬 스타일 CSS 적용
# ==========================================
st.set_page_config(page_title="꾸브라꼬 손익 계산기", layout="wide")

# 꾸브라꼬 브랜드 컬러(레드&화이트) 및 큰 폰트 적용을 위한 CSS
st.markdown("""
    <style>
    .kku-title {
        color: #D1180B;
        font-weight: 900;
        font-size: 2.8rem;
        margin-bottom: -10px;
    }
    .kku-subtitle {
        color: #444;
        font-size: 1.2rem;
        margin-bottom: 20px;
    }
    .card-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 20px;
    }
    .kku-card {
        flex: 1;
        background-color: #ffffff;
        border: 2px solid #D1180B;
        border-radius: 12px;
        padding: 20px 10px;
        text-align: center;
        box-shadow: 3px 3px 10px rgba(209, 24, 11, 0.1);
    }
    .kku-card-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    .kku-card-value {
        font-size: 2.2rem;
        font-weight: 900;
        color: #111;
        margin-bottom: 10px;
    }
    .kku-card-percent {
        font-size: 1.4rem;
        font-weight: bold;
        color: #D1180B;
        background-color: #FFF0F0;
        border-radius: 8px;
        padding: 4px 10px;
        display: inline-block;
    }
    .kku-card-final {
        flex: 1;
        background-color: #D1180B;
        border: 2px solid #D1180B;
        border-radius: 12px;
        padding: 20px 10px;
        text-align: center;
        box-shadow: 3px 3px 15px rgba(209, 24, 11, 0.3);
    }
    .kku-card-final .kku-card-title { color: #ffffff; }
    .kku-card-final .kku-card-value { color: #ffffff; font-size: 2.5rem; }
    .kku-card-final .kku-card-percent {
        color: #D1180B;
        background-color: #ffffff;
        font-size: 1.5rem;
    }
    .formula-box {
        background-color: #f9f9f9;
        border-left: 8px solid #D1180B;
        padding: 20px;
        border-radius: 8px;
        font-size: 1.6rem;
        font-weight: bold;
        color: #222;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="kku-title">🐔🔥 꾸브라꼬 숯불치킨 손익 시뮬레이터</div>', unsafe_allow_html=True)
st.markdown('<div class="kku-subtitle">엑셀 파일을 드래그하여 업로드하고 실시간으로 매장 손익을 분석해보세요!</div>', unsafe_allow_html=True)

# ==========================================
# 2. 파일 업로드 로직
# ==========================================
uploaded_file = st.file_uploader("📂 '가맹점_손익시트.xlsx' 파일을 여기에 드래그하세요.", type=["xlsx"])

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
        st.error(f"엑셀 오류 발생: {e}")
        return None

if uploaded_file is not None:
    df = load_excel_data(uploaded_file)
    
    if df is not None and not df.empty:
        store_list = df["매장명"].astype(str).tolist()

        # ==========================================
        # 3. 매장 선택 및 데이터 연동
        # ==========================================
        st.divider()
        selected_store = st.selectbox("🏪 분석할 매장 선택", options=store_list)
        store_data = df[df["매장명"] == selected_store].iloc[0]

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

        results_container = st.container()
        
        # ==========================================
        # 4. 입력 UI (하단 배치)
        # ==========================================
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
        # 5. 실시간 손익 계산
        # ==========================================
        입금합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타매출
        물류합계 = 물류대 + 기름 + 음료 + 주류
        운영합계 = 인건비 + 월세 + 공과금 + 퀵비 + 포스이용료 + 기타잡비
        
        # 명시된 공식 적용
        최종금액 = 입금합계 - 물류합계 - 운영합계

        # 퍼센트 계산 (모두 월매출 기준)
        입금비율 = (입금합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        물류비율 = (물류합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        운영비율 = (운영합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        수익률 = (최종금액 / 월매출 * 100) if 월매출 > 0 else 0.0

        # ==========================================
        # 6. 상단 결과 요약 화면 렌더링 (커스텀 HTML)
        # ==========================================
        with results_container:
            st.markdown(f"### 📊 [{selected_store}] 매장 시뮬레이션 결과")
            
            # 카드 레이아웃
            html_cards = f"""
            <div class="card-container">
                <div class="kku-card">
                    <div class="kku-card-title">1️⃣ 월 매출액</div>
                    <div class="kku-card-value">{월매출:,.0f} 원</div>
                    <div class="kku-card-percent" style="color:#777; background:#f0f0f0;">(기준금액)</div>
                </div>
                <div class="kku-card">
                    <div class="kku-card-title">2️⃣ 입금 합계</div>
                    <div class="kku-card-value">{입금합계:,.0f} 원</div>
                    <div class="kku-card-percent">매출대비 {입금비율:.1f}%</div>
                </div>
                <div class="kku-card">
                    <div class="kku-card-title">3️⃣ 물류 합계</div>
                    <div class="kku-card-value">{물류합계:,.0f} 원</div>
                    <div class="kku-card-percent">매출대비 {물류비율:.1f}%</div>
                </div>
                <div class="kku-card">
                    <div class="kku-card-title">4️⃣ 운영비 합계</div>
                    <div class="kku-card-value">{운영합계:,.0f} 원</div>
                    <div class="kku-card-percent">매출대비 {운영비율:.1f}%</div>
                </div>
                <div class="kku-card-final">
                    <div class="kku-card-title">🍗 최종 순수익</div>
                    <div class="kku-card-value">{최종금액:,.0f} 원</div>
                    <div class="kku-card-percent">매출대비 {수익률:.1f}%</div>
                </div>
            </div>
            
            <div class="formula-box">
                💡 계산식 : [ 입금 {입금합계:,.0f}원 ] - [ 물류 {물류합계:,.0f}원 ] - [ 운영비 {운영합계:,.0f}원 ] = <span style="color:#D1180B;">최종 순수익 {최종금액:,.0f}원</span>
            </div>
            """
            st.markdown(html_cards, unsafe_allow_html=True)
            st.divider()
            
else:
    st.info("👆 위 영역에 엑셀 파일을 업로드(드래그) 해주세요.")