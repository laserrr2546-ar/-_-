import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. 페이지 설정 및 꾸브라꼬 스타일 CSS 적용
# ==========================================
st.set_page_config(page_title="꾸브라꼬 손익 계산기", layout="wide")

# 꾸브라꼬 브랜드 컬러 및 전체 폰트 확대 CSS
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 1.15rem !important;
    }
    
    .kku-title {
        color: #D1180B;
        font-weight: 900;
        font-size: 3.2rem !important;
        margin-bottom: -5px;
    }
    .kku-subtitle {
        color: #444;
        font-size: 1.4rem !important;
        margin-bottom: 25px;
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
        font-size: 1.4rem !important;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    .kku-card-value {
        font-size: 2.3rem !important;
        font-weight: 900;
        color: #111;
        margin-bottom: 10px;
    }
    .kku-card-percent {
        font-size: 1.4rem !important;
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
    .kku-card-final .kku-card-value { color: #ffffff; font-size: 2.7rem !important; }
    .kku-card-final .kku-card-percent {
        color: #D1180B;
        background-color: #ffffff;
        font-size: 1.5rem !important;
    }
    .formula-box {
        background-color: #f9f9f9;
        border-left: 8px solid #D1180B;
        padding: 20px;
        border-radius: 8px;
        font-size: 1.6rem !important;
        font-weight: bold;
        color: #222;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }
    
    .stNumberInput label, .stSelectbox label {
        font-size: 1.25rem !important;
        font-weight: bold !important;
    }
    div[data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="kku-title">🐔🔥 꾸브라꼬 숯불치킨 손익 시뮬레이터</div>', unsafe_allow_html=True)
st.markdown('<div class="kku-subtitle">엑셀 파일을 드래그하여 업로드하고 실시간으로 매장 손익을 분석해보세요!</div>', unsafe_allow_html=True)

# ==========================================
# 2. 파일 업로드 로직 (가맹점_손익시트_2.xlsx 기준)
# ==========================================
uploaded_file = st.file_uploader("📂 '가맹점_손익시트_2.xlsx' 파일을 여기에 드래그하세요.", type=["xlsx"])

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
        전기세_val = int(store_data.get("전기세", 0))
        가스비_val = int(store_data.get("가스비", 0))
        수도세_val = int(store_data.get("수도세", 0))
        
        퀵비_val = int(store_data.get("퀵비", 0))
        포스이용료_val = int(store_data.get("포스이용료", 0))
        기타잡비_val = int(store_data.get("기타 잡비\n(보험·인터넷·정수기 등)", 0))

        results_container = st.container()
        
        # ==========================================
        # 4. 세부 데이터 입력 및 수정 (기본 정보 그대로 유지)
        # ==========================================
        st.markdown("### 📝 세부 데이터 입력 및 수정 (기본 정보)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🔹 매출 및 플랫폼 입금")
            월매출 = st.number_input("월 매출 (총매출액)", value=월매출_val, step=100000, format="%d")
            배민 = st.number_input("배민 (입금기준)", value=배민_val, step=10000, format="%d")
            요기요 = st.number_input("요기요 (입금기준)", value=요기요_val, step=10000, format="%d")
            쿠팡이츠 = st.number_input("쿠팡이츠 (입금기준)", value=쿠팡이츠_val, step=10000, format="%d")
            땡겨요 = st.number_input("땡겨요 (입금기준)", value=땡겨요_val, step=10000, format="%d")
            위메프오 = st.number_input("위메프오 (입금기준)", value=위메프오_val, step=10000, format="%d")
            포스매출 = st.number_input("포스매출", value=포스매출_val, step=10000, format="%d")
            기타매출 = st.number_input("기타 (먹깨비 등)", value=기타매출_val, step=10000, format="%d")

        with col2:
            st.markdown("#### 🔹 물류 비용")
            물류대 = st.number_input("물류대", value=물류대_val, step=100000, format="%d")
            기름 = st.number_input("기름", value=기름_val, step=10000, format="%d")
            음료 = st.number_input("음료", value=음료_val, step=10000, format="%d")
            주류 = st.number_input("주류", value=주류_val, step=10000, format="%d")

        with col3:
            st.markdown("#### 🔹 운영 비용")
            인건비 = st.number_input("인건비", value=인건비_val, step=100000, format="%d")
            월세 = st.number_input("월세", value=월세_val, step=10000, format="%d")
            전기세 = st.number_input("전기세", value=전기세_val, step=10000, format="%d")
            가스비 = st.number_input("가스비", value=가스비_val, step=10000, format="%d")
            수도세 = st.number_input("수도세", value=수도세_val, step=10000, format="%d")
            퀵비 = st.number_input("퀵비", value=퀵비_val, step=10000, format="%d")
            포스이용료 = st.number_input("포스이용료", value=포스이용료_val, step=1000, format="%d")
            기타잡비 = st.number_input("기타 경비 (보험, 인터넷 등)", value=기타잡비_val, step=10000, format="%d")

        # ==========================================
        # 5. 실시간 손익 계산
        # ==========================================
        입금합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타매출
        물류합계 = 물류대 + 기름 + 음료 + 주류
        운영합계 = 인건비 + 월세 + 전기세 + 가스비 + 수도세 + 퀵비 + 포스이용료 + 기타잡비
        
        최종금액 = 입금합계 - 물류합계 - 운영합계

        입금비율 = (입금합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        물류비율 = (물류합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        운영비율 = (운영합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        수익률 = (최종금액 / 월매출 * 100) if 월매출 > 0 else 0.0

        def calc_pct(val):
            return (val / 월매출 * 100) if 월매출 > 0 else 0.0

        # ==========================================
        # 6. 상단 결과 요약 및 매출대비 물류/운영비 그래프
        # ==========================================
        with results_container:
            st.markdown(f"### 📊 [{selected_store}] 매장 시뮬레이션 결과")
            
            # 요약 카드
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

            # 세부 내역 표
            st.markdown("#### 📋 세부항목별 금액 및 매출 대비 비율(%)")
            d_col1, d_col2, d_col3 = st.columns(3)

            with d_col1:
                st.markdown("**💳 입금 세부 내역**")
                df_income = pd.DataFrame([
                    {"항목": "배민", "금액(원)": f"{배민:,.0f}", "매출대비(%)": f"{calc_pct(배민):.1f}%"},
                    {"항목": "요기요", "금액(원)": f"{요기요:,.0f}", "매출대비(%)": f"{calc_pct(요기요):.1f}%"},
                    {"항목": "쿠팡이츠", "금액(원)": f"{쿠팡이츠:,.0f}", "매출대비(%)": f"{calc_pct(쿠팡이츠):.1f}%"},
                    {"항목": "땡겨요", "금액(원)": f"{땡겨요:,.0f}", "매출대비(%)": f"{calc_pct(땡겨요):.1f}%"},
                    {"항목": "위메프오", "금액(원)": f"{위메프오:,.0f}", "매출대비(%)": f"{calc_pct(위메프오):.1f}%"},
                    {"항목": "포스매출", "금액(원)": f"{포스매출:,.0f}", "매출대비(%)": f"{calc_pct(포스매출):.1f}%"},
                    {"항목": "기타매출", "금액(원)": f"{기타매출:,.0f}", "매출대비(%)": f"{calc_pct(기타매출):.1f}%"},
                ])
                st.dataframe(df_income, hide_index=True, use_container_width=True)

            with d_col2:
                st.markdown("**🚚 물류 세부 내역**")
                df_supply = pd.DataFrame([
                    {"항목": "물류대", "금액(원)": f"{물류대:,.0f}", "매출대비(%)": f"{calc_pct(물류대):.1f}%"},
                    {"항목": "기름", "금액(원)": f"{기름:,.0f}", "매출대비(%)": f"{calc_pct(기름):.1f}%"},
                    {"항목": "음료", "금액(원)": f"{음료:,.0f}", "매출대비(%)": f"{calc_pct(음료):.1f}%"},
                    {"항목": "주류", "금액(원)": f"{주류:,.0f}", "매출대비(%)": f"{calc_pct(주류):.1f}%"},
                ])
                st.dataframe(df_supply, hide_index=True, use_container_width=True)

            with d_col3:
                st.markdown("**🏢 운영비 세부 내역**")
                df_oper = pd.DataFrame([
                    {"항목": "인건비", "금액(원)": f"{인건비:,.0f}", "매출대비(%)": f"{calc_pct(인건비):.1f}%"},
                    {"항목": "월세", "금액(원)": f"{월세:,.0f}", "매출대비(%)": f"{calc_pct(월세):.1f}%"},
                    {"항목": "전기세", "금액(원)": f"{전기세:,.0f}", "매출대비(%)": f"{calc_pct(전기세):.1f}%"},
                    {"항목": "가스비", "금액(원)": f"{가스비:,.0f}", "매출대비(%)": f"{calc_pct(가스비):.1f}%"},
                    {"항목": "수도세", "금액(원)": f"{수도세:,.0f}", "매출대비(%)": f"{calc_pct(수도세):.1f}%"},
                    {"항목": "퀵비", "금액(원)": f"{퀵비:,.0f}", "매출대비(%)": f"{calc_pct(퀵비):.1f}%"},
                    {"항목": "포스이용료", "금액(원)": f"{포스이용료:,.0f}", "매출대비(%)": f"{calc_pct(포스이용료):.1f}%"},
                    {"항목": "기타잡비", "금액(원)": f"{기타잡비:,.0f}", "매출대비(%)": f"{calc_pct(기타잡비):.1f}%"},
                ])
                st.dataframe(df_oper, hide_index=True, use_container_width=True)

            st.divider()

            # 입금을 모두 제외한 매출 대비 물류 / 운영비 세부내역 그래프
            st.markdown("#### 📈 매출 대비 물류 및 운영비 세부내역 분석 그래프")
            g_col1, g_col2 = st.columns(2)

            with g_col1:
                st.markdown("**1. 물류 세부 항목 매출 대비 비율 (%)**")
                supply_dict = {
                    "물류대": calc_pct(물류대),
                    "기름": calc_pct(기름),
                    "음료": calc_pct(음료),
                    "주류": calc_pct(주류)
                }
                supply_labels = list(supply_dict.keys())
                supply_values = list(supply_dict.values())
                supply_amounts = [물류대, 기름, 음료, 주류]

                fig_supply = go.Figure(data=[
                    go.Bar(
                        x=supply_labels,
                        y=supply_values,
                        text=[f"{v:.1f}%<br>({amt:,.0f}원)" for v, amt in zip(supply_values, supply_amounts)],
                        textposition='outside',
                        marker_color="#E65100",
                        textfont=dict(size=14, color='black')
                    )
                ])
                fig_supply.update_layout(
                    xaxis=dict(tickangle=0, tickfont=dict(size=15, color='black')),
                    yaxis=dict(title="매출 대비 비율 (%)", tickfont=dict(size=13)),
                    margin=dict(l=20, r=20, t=30, b=40),
                    height=390,
                    plot_bgcolor="rgba(245,245,245,0.5)"
                )
                st.plotly_chart(fig_supply, use_container_width=True)

            with g_col2:
                st.markdown("**2. 운영비 세부 항목 매출 대비 비율 (%)**")
                oper_dict = {
                    "인건비": calc_pct(인건비),
                    "월세": calc_pct(월세),
                    "전기세": calc_pct(전기세),
                    "가스비": calc_pct(가스비),
                    "수도세": calc_pct(수도세),
                    "퀵비": calc_pct(퀵비),
                    "포스이용료": calc_pct(포스이용료),
                    "기타잡비": calc_pct(기타잡비)
                }
                # 비율이 높은 순서로 정렬
                sorted_oper = sorted(oper_dict.items(), key=lambda x: x[1], reverse=True)
                oper_labels = [x[0] for x in sorted_oper]
                oper_values = [x[1] for x in sorted_oper]
                
                # 금액 매핑
                amount_map = {
                    "인건비": 인건비, "월세": 월세, "전기세": 전기세, "가스비": 가스비,
                    "수도세": 수도세, "퀵비": 퀵비, "포스이용료": 포스이용료, "기타잡비": 기타잡비
                }
                oper_amounts = [amount_map[k] for k in oper_labels]

                fig_oper = go.Figure(data=[
                    go.Bar(
                        x=oper_labels,
                        y=oper_values,
                        text=[f"{v:.1f}%<br>({amt:,.0f}원)" for v, amt in zip(oper_values, oper_amounts)],
                        textposition='outside',
                        marker_color="#C62828",
                        textfont=dict(size=13, color='black')
                    )
                ])
                fig_oper.update_layout(
                    xaxis=dict(tickangle=0, tickfont=dict(size=14, color='black')),
                    yaxis=dict(title="매출 대비 비율 (%)", tickfont=dict(size=13)),
                    margin=dict(l=20, r=20, t=30, b=40),
                    height=390,
                    plot_bgcolor="rgba(245,245,245,0.5)"
                )
                st.plotly_chart(fig_oper, use_container_width=True)

            st.divider()

else:
    st.info("👆 위 영역에 엑셀 파일('가맹점_손익시트_2.xlsx')을 업로드(드래그) 해주세요.")