import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. 페이지 설정 및 미미순두부 스타일 CSS 적용
# ==========================================
st.set_page_config(page_title="미미순두부 손익 계산기", layout="wide")

# 미미순두부 브랜드 컬러(레드/오렌지 계열) 및 전체 폰트 확대 CSS
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 1.15rem !important;
    }
    
    .mimi-title {
        color: #E65100;
        font-weight: 900;
        font-size: 3.2rem !important;
        margin-bottom: -5px;
    }
    .mimi-subtitle {
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
    .mimi-card {
        flex: 1;
        background-color: #ffffff;
        border: 2px solid #E65100;
        border-radius: 12px;
        padding: 20px 10px;
        text-align: center;
        box-shadow: 3px 3px 10px rgba(230, 81, 0, 0.1);
    }
    .mimi-card-title {
        font-size: 1.4rem !important;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    .mimi-card-value {
        font-size: 2.3rem !important;
        font-weight: 900;
        color: #111;
        margin-bottom: 10px;
    }
    .mimi-card-percent {
        font-size: 1.4rem !important;
        font-weight: bold;
        color: #E65100;
        background-color: #FFF3E0;
        border-radius: 8px;
        padding: 4px 10px;
        display: inline-block;
    }
    .mimi-card-final {
        flex: 1;
        background-color: #E65100;
        border: 2px solid #E65100;
        border-radius: 12px;
        padding: 20px 10px;
        text-align: center;
        box-shadow: 3px 3px 15px rgba(230, 81, 0, 0.3);
    }
    .mimi-card-final .mimi-card-title { color: #ffffff; }
    .mimi-card-final .mimi-card-value { color: #ffffff; font-size: 2.7rem !important; }
    .mimi-card-final .mimi-card-percent {
        color: #E65100;
        background-color: #ffffff;
        font-size: 1.5rem !important;
    }
    .formula-box {
        background-color: #f9f9f9;
        border-left: 8px solid #E65100;
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

st.markdown('<div class="mimi-title">🍲🔥 미미순두부 손익 시뮬레이터</div>', unsafe_allow_html=True)
st.markdown('<div class="mimi-subtitle">엑셀 파일을 드래그하여 업로드하고 실시간으로 매장 손익을 분석해보세요!</div>', unsafe_allow_html=True)

# ==========================================
# 2. 파일 업로드 로직 (가맹점_손익시트 (미미).xlsx 기준)
# ==========================================
uploaded_file = st.file_uploader("📂 '가맹점_손익시트 (미미).xlsx' 파일을 여기에 드래그하세요.", type=["xlsx"])

@st.cache_data
def load_excel_data(file):
    try:
        df = pd.read_excel(file, sheet_name="손익 시트 미미순두부", header=3)
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

        인건비_val = int(store_data.get("인건비", 0))
        기름_val = int(store_data.get("기름", 0))
        음료_val = int(store_data.get("음료", 0))
        주류_val = int(store_data.get("주류", 0))
        월세_val = int(store_data.get("월세", 0))
        전기세_val = int(store_data.get("전기세", 0))
        가스비_val = int(store_data.get("가스비", 0))
        수도세_val = int(store_data.get("수도세", 0))
        마케팅비용_val = int(store_data.get("마케팅비용", 0))
        포스이용료_val = int(store_data.get("포스이용료", 0))
        부가세_val = int(store_data.get("부가세", 0))
        종소세_val = int(store_data.get("종소세", 0))
        퇴직금세이브_val = int(store_data.get("퇴직금세이브", 0))
        기타잡비_val = int(store_data.get("기타 잡비\n(보험·인터넷·정수기 등)", 0))

        results_container = st.container()
        
        # ==========================================
        # 4. 세부 데이터 입력 및 수정
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

        with col3:
            st.markdown("#### 🔹 운영 및 기타 비용")
            인건비 = st.number_input("인건비", value=인건비_val, step=100000, format="%d")
            기름 = st.number_input("기름", value=기름_val, step=10000, format="%d")
            음료 = st.number_input("음료", value=음료_val, step=10000, format="%d")
            주류 = st.number_input("주류", value=주류_val, step=10000, format="%d")
            월세 = st.number_input("월세", value=월세_val, step=10000, format="%d")
            전기세 = st.number_input("전기세", value=전기세_val, step=10000, format="%d")
            가스비 = st.number_input("가스비", value=가스비_val, step=10000, format="%d")
            수도세 = st.number_input("수도세", value=수도세_val, step=10000, format="%d")
            마케팅비용 = st.number_input("마케팅비용", value=마케팅비용_val, step=10000, format="%d")
            포스이용료 = st.number_input("포스이용료", value=포스이용료_val, step=1000, format="%d")
            부가세 = st.number_input("부가세", value=부가세_val, step=10000, format="%d")
            종소세 = st.number_input("종소세", value=종소세_val, step=10000, format="%d")
            퇴직금세이브 = st.number_input("퇴직금세이브", value=퇴직금세이브_val, step=10000, format="%d")
            기타잡비 = st.number_input("기타 경비 (보험, 인터넷 등)", value=기타잡비_val, step=10000, format="%d")

        # ==========================================
        # 5. 실시간 손익 계산
        # ==========================================
        입금합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타매출
        물류합계 = 물류대  # 미미순두부 시트 기준 물류 합계는 물류대 중심
        운영합계 = 인건비 + 기름 + 음료 + 주류 + 월세 + 전기세 + 가스비 + 수도세 + 마케팅비용 + 포스이용료 + 부가세 + 종소세 + 퇴직금세이브 + 기타잡비
        
        최종금액 = 입금합계 - 물류합계 - 운영합계

        입금비율 = (입금합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        물류비율 = (물류합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        운영비율 = (운영합계 / 월매출 * 100) if 월매출 > 0 else 0.0
        수익률 = (최종금액 / 월매출 * 100) if 월매출 > 0 else 0.0

        def calc_pct(val):
            return (val / 월매출 * 100) if 월매출 > 0 else 0.0

        # ==========================================
        # 6. 상단 결과 요약 및 그래프
        # ==========================================
        with results_container:
            st.markdown(f"### 📊 [{selected_store}] 매장 시뮬레이션 결과")
            
            html_cards = f"""
            <div class="card-container">
                <div class="mimi-card">
                    <div class="mimi-card-title">1️⃣ 월 매출액</div>
                    <div class="mimi-card-value">{월매출:,.0f} 원</div>
                    <div class="mimi-card-percent" style="color:#777; background:#f0f0f0;">(기준금액)</div>
                </div>
                <div class="mimi-card">
                    <div class="mimi-card-title">2️⃣ 입금 합계</div>
                    <div class="mimi-card-value">{입금합계:,.0f} 원</div>
                    <div class="mimi-card-percent">매출대비 {입금비율:.1f}%</div>
                </div>
                <div class="mimi-card">
                    <div class="mimi-card-title">3️⃣ 물류 합계</div>
                    <div class="mimi-card-value">{물류합계:,.0f} 원</div>
                    <div class="mimi-card-percent">매출대비 {물류비율:.1f}%</div>
                </div>
                <div class="mimi-card">
                    <div class="mimi-card-title">4️⃣ 운영비 합계</div>
                    <div class="mimi-card-value">{운영합계:,.0f} 원</div>
                    <div class="mimi-card-percent">매출대비 {운영비율:.1f}%</div>
                </div>
                <div class="mimi-card-final">
                    <div class="mimi-card-title">🍲 최종 순수익</div>
                    <div class="mimi-card-value">{최종금액:,.0f} 원</div>
                    <div class="mimi-card-percent">매출대비 {수익률:.1f}%</div>
                </div>
            </div>
            
            <div class="formula-box">
                💡 계산식 : [ 입금 {입금합계:,.0f}원 ] - [ 물류 {물류합계:,.0f}원 ] - [ 운영비 {운영합계:,.0f}원 ] = <span style="color:#E65100;">최종 순수익 {최종금액:,.0f}원</span>
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
                ])
                st.dataframe(df_supply, hide_index=True, use_container_width=True)

            with d_col3:
                st.markdown("**🏢 운영비 세부 내역**")
                df_oper = pd.DataFrame([
                    {"항목": "인건비", "금액(원)": f"{인건비:,.0f}", "매출대비(%)": f"{calc_pct(인건비):.1f}%"},
                    {"항목": "기름", "금액(원)": f"{기름:,.0f}", "매출대비(%)": f"{calc_pct(기름):.1f}%"},
                    {"항목": "음료", "금액(원)": f"{음료:,.0f}", "매출대비(%)": f"{calc_pct(음료):.1f}%"},
                    {"항목": "주류", "금액(원)": f"{주류:,.0f}", "매출대비(%)": f"{calc_pct(주류):.1f}%"},
                    {"항목": "월세", "금액(원)": f"{월세:,.0f}", "매출대비(%)": f"{calc_pct(월세):.1f}%"},
                    {"항목": "전기세", "금액(원)": f"{전기세:,.0f}", "매출대비(%)": f"{calc_pct(전기세):.1f}%"},
                    {"항목": "가스비", "금액(원)": f"{가스비:,.0f}", "매출대비(%)": f"{calc_pct(가스비):.1f}%"},
                    {"항목": "수도세", "금액(원)": f"{수도세:,.0f}", "매출대비(%)": f"{calc_pct(수도세):.1f}%"},
                    {"항목": "마케팅비용", "금액(원)": f"{마케팅비용:,.0f}", "매출대비(%)": f"{calc_pct(마케팅비용):.1f}%"},
                    {"항목": "포스이용료", "금액(원)": f"{포스이용료:,.0f}", "매출대비(%)": f"{calc_pct(포스이용료):.1f}%"},
                    {"항목": "부가세", "금액(원)": f"{부가세:,.0f}", "매출대비(%)": f"{calc_pct(부가세):.1f}%"},
                    {"항목": "종소세", "금액(원)": f"{종소세:,.0f}", "매출대비(%)": f"{calc_pct(종소세):.1f}%"},
                    {"항목": "퇴직금세이브", "금액(원)": f"{퇴직금세이브:,.0f}", "매출대비(%)": f"{calc_pct(퇴직금세이브):.1f}%"},
                    {"항목": "기타잡비", "금액(원)": f"{기타잡비:,.0f}", "매출대비(%)": f"{calc_pct(기타잡비):.1f}%"},
                ])
                st.dataframe(df_oper, hide_index=True, use_container_width=True)

            st.divider()

            # 운영비 세부항목 분석 그래프 (비율 높은 순서로 정렬)
            st.markdown("#### 📈 운영비 세부 항목 매출 대비 비율 (%) 분석 그래프")
            
            oper_dict = {
                "인건비": calc_pct(인건비),
                "기름": calc_pct(기름),
                "음료": calc_pct(음료),
                "주류": calc_pct(주류),
                "월세": calc_pct(월세),
                "전기세": calc_pct(전기세),
                "가스비": calc_pct(가스비),
                "수도세": calc_pct(수도세),
                "마케팅비용": calc_pct(마케팅비용),
                "포스이용료": calc_pct(포스이용료),
                "부가세": calc_pct(부가세),
                "종소세": calc_pct(종소세),
                "퇴직금세이브": calc_pct(퇴직금세이브),
                "기타잡비": calc_pct(기타잡비)
            }
            sorted_oper = sorted(oper_dict.items(), key=lambda x: x[1], reverse=True)
            oper_labels = [x[0] for x in sorted_oper]
            oper_values = [x[1] for x in sorted_oper]
            
            amount_map = {
                "인건비": 인건비, "기름": 기름, "음료": 음료, "주류": 주류, "월세": 월세,
                "전기세": 전기세, "가스비": 가스비, "수도세": 수도세, "마케팅비용": 마케팅비용,
                "포스이용료": 포스이용료, "부가세": 부가세, "종소세": 종소세,
                "퇴직금세이브": 퇴직금세이브, "기타잡비": 기타잡비
            }
            oper_amounts = [amount_map[k] for k in oper_labels]

            fig_oper = go.Figure(data=[
                go.Bar(
                    x=oper_labels,
                    y=oper_values,
                    text=[f"{v:.1f}%<br>({amt:,.0f}원)" for v, amt in zip(oper_values, oper_amounts)],
                    textposition='outside',
                    marker_color="#E65100",
                    textfont=dict(size=12, color='black')
                )
            ])
            fig_oper.update_layout(
                xaxis=dict(tickangle=-30, tickfont=dict(size=13, color='black')),
                yaxis=dict(title="매출 대비 비율 (%)", tickfont=dict(size=13)),
                margin=dict(l=20, r=20, t=30, b=60),
                height=450,
                plot_bgcolor="rgba(245,245,245,0.5)"
            )
            st.plotly_chart(fig_oper, use_container_width=True)

            st.divider()

else:
    st.info("👆 위 영역에 미미순두부 손익 엑셀 파일('가맹점_손익시트 (미미).xlsx')을 업로드(드래그) 해주세요.")