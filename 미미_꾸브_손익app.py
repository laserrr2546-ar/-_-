import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 0. 페이지 설정 (전체 레이아웃)
# ==========================================
st.set_page_config(page_title="브랜드 통합 손익 계산기", layout="wide")

# 공통 및 브랜드별 스타일 CSS 적용
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 1.15rem !important;
    }
    
    /* 꾸브라꼬 스타일 */
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
    .kku-card {
        flex: 1; background-color: #ffffff; border: 2px solid #D1180B; border-radius: 12px; padding: 20px 10px; text-align: center; box-shadow: 3px 3px 10px rgba(209, 24, 11, 0.1);
    }
    .kku-card-final {
        flex: 1; background-color: #D1180B; border: 2px solid #D1180B; border-radius: 12px; padding: 20px 10px; text-align: center; box-shadow: 3px 3px 15px rgba(209, 24, 11, 0.3);
    }
    .kku-card-final .card-title { color: #ffffff; }
    .kku-card-final .card-value { color: #ffffff; font-size: 2.5rem !important; }
    .kku-card-final .card-percent { color: #D1180B; background-color: #ffffff; font-size: 1.4rem !important; }
    .kku-formula-box {
        background-color: #f9f9f9; border-left: 8px solid #D1180B; padding: 20px; border-radius: 8px; font-size: 1.6rem !important; font-weight: bold; color: #222; text-align: center; margin-bottom: 30px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }

    /* 미미순두부 스타일 */
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
    .mimi-card {
        flex: 1; background-color: #ffffff; border: 2px solid #E65100; border-radius: 12px; padding: 20px 10px; text-align: center; box-shadow: 3px 3px 10px rgba(230, 81, 0, 0.1);
    }
    .mimi-card-final {
        flex: 1; background-color: #E65100; border: 2px solid #E65100; border-radius: 12px; padding: 20px 10px; text-align: center; box-shadow: 3px 3px 15px rgba(230, 81, 0, 0.3);
    }
    .mimi-card-final .card-title { color: #ffffff; }
    .mimi-card-final .card-value { color: #ffffff; font-size: 2.5rem !important; }
    .mimi-card-final .card-percent { color: #E65100; background-color: #ffffff; font-size: 1.4rem !important; }
    .mimi-formula-box {
        background-color: #f9f9f9; border-left: 8px solid #E65100; padding: 20px; border-radius: 8px; font-size: 1.6rem !important; font-weight: bold; color: #222; text-align: center; margin-bottom: 30px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }

    /* 공통 카드 구성요소 스타일 */
    .card-container { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 20px; }
    .card-title { font-size: 1.25rem !important; font-weight: bold; color: #333; margin-bottom: 8px; }
    .card-value { font-size: 2.0rem !important; font-weight: 900; color: #111; margin-bottom: 8px; }
    .card-percent { font-size: 1.2rem !important; font-weight: bold; border-radius: 8px; padding: 3px 8px; display: inline-block; }
    
    .stNumberInput label, .stSelectbox label { font-size: 1.25rem !important; font-weight: bold !important; }
    div[data-testid="stMarkdownContainer"] p { font-size: 1.2rem !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 탭 생성 (꾸브라꼬 / 미미순두부)
# ==========================================
tab_kku, tab_mimi = st.tabs(["🐔 꾸브라꼬 숯불치킨", "🍲 미미순두부"])

# ==========================================
# [TAB 1] 꾸브라꼬 숯불치킨 로직
# ==========================================
with tab_kku:
    st.markdown('<div class="kku-title">🐔🔥 꾸브라꼬 숯불치킨 손익 시뮬레이터</div>', unsafe_allow_html=True)
    st.markdown('<div class="kku-subtitle">꾸브라꼬 가맹점 엑셀 파일을 업로드하고 실시간 손익을 분석해보세요!</div>', unsafe_allow_html=True)

    uploaded_file_kku = st.file_uploader("📂 '가맹점_손익시트_2.xlsx' 파일을 여기에 드래그하세요.", type=["xlsx"], key="kku_uploader")

    @st.cache_data
    def load_kku_data(file):
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

    if uploaded_file_kku is not None:
        df_kku = load_kku_data(uploaded_file_kku)
        
        if df_kku is not None and not df_kku.empty:
            store_list_kku = df_kku["매장명"].astype(str).tolist()

            st.divider()
            selected_store_kku = st.selectbox("🏪 분석할 매장 선택 (꾸브라꼬)", options=store_list_kku, key="kku_store")
            store_data_kku = df_kku[df_kku["매장명"] == selected_store_kku].iloc[0]

            월매출_v = int(store_data_kku.get("월 매출", 0))
            배민_v = int(store_data_kku.get("배민\n(입금기준)", 0))
            요기요_v = int(store_data_kku.get("요기요\n(입금기준)", 0))
            쿠팡이츠_v = int(store_data_kku.get("쿠팡이츠\n(입금기준)", 0))
            땡겨요_v = int(store_data_kku.get("땡겨요\n(입금기준)", 0))
            위메프오_v = int(store_data_kku.get("위메프오\n(입금기준)", 0))
            포스매출_v = int(store_data_kku.get("포스매출", 0))
            기타매출_v = int(store_data_kku.get("기타\n(먹깨비, 울산페달, 양산배달)", 0))
            
            물류대_v = int(store_data_kku.get("물류대", 0))
            기름_v = int(store_data_kku.get("기름", 0))
            음료_v = int(store_data_kku.get("음료", 0))
            주류_v = int(store_data_kku.get("주류", 0))

            인건비_v = int(store_data_kku.get("인건비", 0))
            월세_v = int(store_data_kku.get("월세", 0))
            전기세_v = int(store_data_kku.get("전기세", 0))
            가스비_v = int(store_data_kku.get("가스비", 0))
            수도세_v = int(store_data_kku.get("수도세", 0))
            퀵비_v = int(store_data_kku.get("퀵비", 0))
            포스이용료_v = int(store_data_kku.get("포스이용료", 0))
            기타잡비_v = int(store_data_kku.get("기타 잡비\n(보험·인터넷·정수기 등)", 0))

            results_container_kku = st.container()
            
            st.markdown("### 📝 세부 데이터 입력 및 수정")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🔹 매출 및 플랫폼 입금")
                월매출 = st.number_input("월 매출 (총매출액)", value=월매출_v, step=100000, format="%d", key="kku_1")
                배민 = st.number_input("배민 (입금기준)", value=배민_v, step=10000, format="%d", key="kku_2")
                요기요 = st.number_input("요기요 (입금기준)", value=요기요_v, step=10000, format="%d", key="kku_3")
                쿠팡이츠 = st.number_input("쿠팡이츠 (입금기준)", value=쿠팡이츠_v, step=10000, format="%d", key="kku_4")
                땡겨요 = st.number_input("땡겨요 (입금기준)", value=땡겨요_v, step=10000, format="%d", key="kku_5")
                위메프오 = st.number_input("위메프오 (입금기준)", value=위메프오_v, step=10000, format="%d", key="kku_6")
                포스매출 = st.number_input("포스매출", value=포스매출_v, step=10000, format="%d", key="kku_7")
                기타매출 = st.number_input("기타 (먹깨비 등)", value=기타매출_v, step=10000, format="%d", key="kku_8")

            with col2:
                st.markdown("#### 🔹 물류 비용")
                물류대 = st.number_input("물류대", value=물류대_v, step=100000, format="%d", key="kku_9")
                기름 = st.number_input("기름", value=기름_v, step=10000, format="%d", key="kku_10")
                음료 = st.number_input("음료", value=음료_v, step=10000, format="%d", key="kku_11")
                주류 = st.number_input("주류", value=주류_v, step=10000, format="%d", key="kku_12")

            with col3:
                st.markdown("#### 🔹 운영 비용")
                인건비 = st.number_input("인건비", value=인건비_v, step=100000, format="%d", key="kku_13")
                월세 = st.number_input("월세", value=월세_v, step=10000, format="%d", key="kku_14")
                전기세 = st.number_input("전기세", value=전기세_v, step=10000, format="%d", key="kku_15")
                가스비 = st.number_input("가스비", value=가스비_v, step=10000, format="%d", key="kku_16")
                수도세 = st.number_input("수도세", value=수도세_v, step=10000, format="%d", key="kku_17")
                퀵비 = st.number_input("퀵비", value=퀵비_v, step=10000, format="%d", key="kku_18")
                포스이용료 = st.number_input("포스이용료", value=포스이용료_v, step=1000, format="%d", key="kku_19")
                기타잡비 = st.number_input("기타 경비", value=기타잡비_v, step=10000, format="%d", key="kku_20")

            입금합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타매출
            물류합계 = 물류대 + 기름 + 음료 + 주류
            운영합계 = 인건비 + 월세 + 전기세 + 가스비 + 수도세 + 퀵비 + 포스이용료 + 기타잡비
            최종금액 = 입금합계 - 물류합계 - 운영합계

            입금비율 = (입금합계 / 월매출 * 100) if 월매출 > 0 else 0.0
            물류비율 = (물류합계 / 월매출 * 100) if 월매출 > 0 else 0.0
            인건비율 = (인건비 / 월매출 * 100) if 월매출 > 0 else 0.0
            운영비율 = (운영합계 / 월매출 * 100) if 월매출 > 0 else 0.0
            수익률 = (최종금액 / 월매출 * 100) if 월매출 > 0 else 0.0

            def calc_pct_kku(val):
                return (val / 월매출 * 100) if 월매출 > 0 else 0.0

            with results_container_kku:
                st.markdown(f"### 📊 [{selected_store_kku}] 매장 시뮬레이션 결과")
                
                html_cards_kku = f"""
                <div class="card-container">
                    <div class="kku-card">
                        <div class="card-title">1️⃣ 월 매출액</div>
                        <div class="card-value">{월매출:,.0f} 원</div>
                        <div class="card-percent" style="color:#777; background:#f0f0f0;">(기준금액)</div>
                    </div>
                    <div class="kku-card">
                        <div class="card-title">2️⃣ 입금 합계</div>
                        <div class="card-value">{입금합계:,.0f} 원</div>
                        <div class="card-percent" style="color:#D1180B; background-color:#FFF0F0;">매출대비 {입금비율:.1f}%</div>
                    </div>
                    <div class="kku-card">
                        <div class="card-title">3️⃣ 물류 합계</div>
                        <div class="card-value">{물류합계:,.0f} 원</div>
                        <div class="card-percent" style="color:#D1180B; background-color:#FFF0F0;">매출대비 {물류비율:.1f}%</div>
                    </div>
                    <div class="kku-card">
                        <div class="card-title">4️⃣ 인건비</div>
                        <div class="card-value">{인건비:,.0f} 원</div>
                        <div class="card-percent" style="color:#D1180B; background-color:#FFF0F0;">매출대비 {인건비율:.1f}%</div>
                    </div>
                    <div class="kku-card">
                        <div class="card-title">5️⃣ 운영비 합계</div>
                        <div class="card-value">{운영합계:,.0f} 원</div>
                        <div class="card-percent" style="color:#D1180B; background-color:#FFF0F0;">매출대비 {운영비율:.1f}%</div>
                    </div>
                    <div class="kku-card-final">
                        <div class="card-title">🍗 최종 순수익</div>
                        <div class="card-value">{최종금액:,.0f} 원</div>
                        <div class="card-percent">매출대비 {수익률:.1f}%</div>
                    </div>
                </div>
                
                <div class="kku-formula-box">
                    💡 계산식 : [ 입금 {입금합계:,.0f}원 ] - [ 물류 {물류합계:,.0f}원 ] - [ 운영비 {운영합계:,.0f}원 ] = <span style="color:#D1180B;">최종 순수익 {최종금액:,.0f}원</span>
                </div>
                """
                st.markdown(html_cards_kku, unsafe_allow_html=True)

                # 세부 내역 표
                st.markdown("#### 📋 세부항목별 금액 및 매출 대비 비율(%)")
                d_col1, d_col2, d_col3 = st.columns(3)

                with d_col1:
                    st.markdown("**💳 입금 세부 내역**")
                    df_income = pd.DataFrame([
                        {"항목": "배민", "금액(원)": f"{배민:,.0f}", "매출대비(%)": f"{calc_pct_kku(배민):.1f}%"},
                        {"항목": "요기요", "금액(원)": f"{요기요:,.0f}", "매출대비(%)": f"{calc_pct_kku(요기요):.1f}%"},
                        {"항목": "쿠팡이츠", "금액(원)": f"{쿠팡이츠:,.0f}", "매출대비(%)": f"{calc_pct_kku(쿠팡이츠):.1f}%"},
                        {"항목": "땡겨요", "금액(원)": f"{땡겨요:,.0f}", "매출대비(%)": f"{calc_pct_kku(땡겨요):.1f}%"},
                        {"항목": "위메프오", "금액(원)": f"{위메프오:,.0f}", "매출대비(%)": f"{calc_pct_kku(위메프오):.1f}%"},
                        {"항목": "포스매출", "금액(원)": f"{포스매출:,.0f}", "매출대비(%)": f"{calc_pct_kku(포스매출):.1f}%"},
                        {"항목": "기타매출", "금액(원)": f"{기타매출:,.0f}", "매출대비(%)": f"{calc_pct_kku(기타매출):.1f}%"},
                    ])
                    st.dataframe(df_income, hide_index=True, use_container_width=True)

                with d_col2:
                    st.markdown("**🚚 물류 세부 내역**")
                    df_supply = pd.DataFrame([
                        {"항목": "물류대", "금액(원)": f"{물류대:,.0f}", "매출대비(%)": f"{calc_pct_kku(물류대):.1f}%"},
                        {"항목": "기름", "금액(원)": f"{기름:,.0f}", "매출대비(%)": f"{calc_pct_kku(기름):.1f}%"},
                        {"항목": "음료", "금액(원)": f"{음료:,.0f}", "매출대비(%)": f"{calc_pct_kku(음료):.1f}%"},
                        {"항목": "주류", "금액(원)": f"{주류:,.0f}", "매출대비(%)": f"{calc_pct_kku(주류):.1f}%"},
                    ])
                    st.dataframe(df_supply, hide_index=True, use_container_width=True)

                with d_col3:
                    st.markdown("**🏢 운영비 세부 내역**")
                    df_oper = pd.DataFrame([
                        {"항목": "인건비", "금액(원)": f"{인건비:,.0f}", "매출대비(%)": f"{calc_pct_kku(인건비):.1f}%"},
                        {"항목": "월세", "금액(원)": f"{월세:,.0f}", "매출대비(%)": f"{calc_pct_kku(월세):.1f}%"},
                        {"항목": "전기세", "금액(원)": f"{전기세:,.0f}", "매출대비(%)": f"{calc_pct_kku(전기세):.1f}%"},
                        {"항목": "가스비", "금액(원)": f"{가스비:,.0f}", "매출대비(%)": f"{calc_pct_kku(가스비):.1f}%"},
                        {"항목": "수도세", "금액(원)": f"{수도세:,.0f}", "매출대비(%)": f"{calc_pct_kku(수도세):.1f}%"},
                        {"항목": "퀵비", "금액(원)": f"{퀵비:,.0f}", "매출대비(%)": f"{calc_pct_kku(퀵비):.1f}%"},
                        {"항목": "포스이용료", "금액(원)": f"{포스이용료:,.0f}", "매출대비(%)": f"{calc_pct_kku(포스이용료):.1f}%"},
                        {"항목": "기타잡비", "금액(원)": f"{기타잡비:,.0f}", "매출대비(%)": f"{calc_pct_kku(기타잡비):.1f}%"},
                    ])
                    st.dataframe(df_oper, hide_index=True, use_container_width=True)

                st.divider()

                # 그래프
                st.markdown("#### 📈 매출 대비 물류 및 운영비 세부내역 분석 그래프")
                g_col1, g_col2 = st.columns(2)

                with g_col1:
                    st.markdown("**1. 물류 세부 항목 매출 대비 비율 (%)**")
                    sup_dict = {"물류대": calc_pct_kku(물류대), "기름": calc_pct_kku(기름), "음료": calc_pct_kku(음료), "주류": calc_pct_kku(주류)}
                    fig_sup = go.Figure(data=[go.Bar(x=list(sup_dict.keys()), y=list(sup_dict.values()), text=[f"{v:.1f}%<br>({amt:,.0f}원)" for v, amt in zip(sup_dict.values(), [물류대, 기름, 음료, 주류])], textposition='outside', marker_color="#E65100")])
                    fig_sup.update_layout(xaxis=dict(tickfont=dict(size=14)), yaxis=dict(title="비율 (%)"), height=390, margin=dict(l=20, r=20, t=30, b=40), plot_bgcolor="rgba(245,245,245,0.5)")
                    st.plotly_chart(fig_sup, use_container_width=True)

                with g_col2:
                    st.markdown("**2. 운영비 세부 항목 매출 대비 비율 (%)**")
                    op_dict = {"인건비": calc_pct_kku(인건비), "월세": calc_pct_kku(월세), "전기세": calc_pct_kku(전기세), "가스비": calc_pct_kku(가스비), "수도세": calc_pct_kku(수도세), "퀵비": calc_pct_kku(퀵비), "포스이용료": calc_pct_kku(포스이용료), "기타잡비": calc_pct_kku(기타잡비)}
                    sorted_op = sorted(op_dict.items(), key=lambda x: x[1], reverse=True)
                    op_l, op_v = [x[0] for x in sorted_op], [x[1] for x in sorted_op]
                    op_amt_map = {"인건비": 인건비, "월세": 월세, "전기세": 전기세, "가스비": 가스비, "수도세": 수도세, "퀵비": 퀵비, "포스이용료": 포스이용료, "기타잡비": 기타잡비}
                    op_amts = [op_amt_map[k] for k in op_l]
                    
                    fig_op = go.Figure(data=[go.Bar(x=op_l, y=op_v, text=[f"{v:.1f}%<br>({amt:,.0f}원)" for v, amt in zip(op_v, op_amts)], textposition='outside', marker_color="#C62828")])
                    fig_op.update_layout(xaxis=dict(tickfont=dict(size=13)), yaxis=dict(title="비율 (%)"), height=390, margin=dict(l=20, r=20, t=30, b=40), plot_bgcolor="rgba(245,245,245,0.5)")
                    st.plotly_chart(fig_op, use_container_width=True)
    else:
        st.info("👆 위 영역에 꾸브라꼬 손익 엑셀 파일을 업로드해주세요.")


# ==========================================
# [TAB 2] 미미순두부 로직
# ==========================================
with tab_mimi:
    st.markdown('<div class="mimi-title">🍲🔥 미미순두부 손익 시뮬레이터</div>', unsafe_allow_html=True)
    st.markdown('<div class="mimi-subtitle">미미순두부 손익 엑셀 파일을 업로드하고 실시간 손익을 분석해보세요!</div>', unsafe_allow_html=True)

    uploaded_file_mimi = st.file_uploader("📂 '가맹점_손익시트 (미미).xlsx' 파일을 여기에 드래그하세요.", type=["xlsx"], key="mimi_uploader")

    @st.cache_data
    def load_mimi_data(file):
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

    if uploaded_file_mimi is not None:
        df_m = load_mimi_data(uploaded_file_mimi)
        
        if df_m is not None and not df_m.empty:
            store_list_mimi = df_m["매장명"].astype(str).tolist()

            st.divider()
            selected_store_mimi = st.selectbox("🏪 분석할 매장 선택 (미미순두부)", options=store_list_mimi, key="mimi_store")
            store_data_m = df_m[df_m["매장명"] == selected_store_mimi].iloc[0]

            m_월매출 = int(store_data_m.get("월 매출", 0))
            m_배민 = int(store_data_m.get("배민\n(입금기준)", 0))
            m_요기요 = int(store_data_m.get("요기요\n(입금기준)", 0))
            m_쿠팡이츠 = int(store_data_m.get("쿠팡이츠\n(입금기준)", 0))
            m_땡겨요 = int(store_data_m.get("땡겨요\n(입금기준)", 0))
            m_위메프오 = int(store_data_m.get("위메프오\n(입금기준)", 0))
            m_포스매출 = int(store_data_m.get("포스매출", 0))
            m_기타매출 = int(store_data_m.get("기타\n(먹깨비, 울산페달, 양산배달)", 0))
            
            m_물류대 = int(store_data_m.get("물류대", 0))
            m_기름 = int(store_data_m.get("기름", 0))
            m_음료 = int(store_data_m.get("음료", 0))
            m_주류 = int(store_data_m.get("주류", 0))

            m_인건비 = int(store_data_m.get("인건비", 0))
            m_월세 = int(store_data_m.get("월세", 0))
            m_전기세 = int(store_data_m.get("전기세", 0))
            m_가스비 = int(store_data_m.get("가스비", 0))
            m_수도세 = int(store_data_m.get("수도세", 0))
            m_마케팅비용 = int(store_data_m.get("마케팅비용", 0))
            m_포스이용료 = int(store_data_m.get("포스이용료", 0))
            m_부가세 = int(store_data_m.get("부가세", 0))
            m_종소세 = int(store_data_m.get("종소세", 0))
            m_퇴직금세이브 = int(store_data_m.get("퇴직금세이브", 0))
            m_기타잡비 = int(store_data_m.get("기타 잡비\n(보험·인터넷·정수기 등)", 0))

            results_container_mimi = st.container()
            
            st.markdown("### 📝 세부 데이터 입력 및 수정")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🔹 매출 및 플랫폼 입금")
                월매출 = st.number_input("월 매출 (총매출액)", value=m_월매출, step=100000, format="%d", key="m_1")
                배민 = st.number_input("배민 (입금기준)", value=m_배민, step=10000, format="%d", key="m_2")
                요기요 = st.number_input("요기요 (입금기준)", value=m_요기요, step=10000, format="%d", key="m_3")
                쿠팡이츠 = st.number_input("쿠팡이츠 (입금기준)", value=m_쿠팡이츠, step=10000, format="%d", key="m_4")
                땡겨요 = st.number_input("땡겨요 (입금기준)", value=m_땡겨요, step=10000, format="%d", key="m_5")
                위메프오 = st.number_input("위메프오 (입금기준)", value=m_위메프오, step=10000, format="%d", key="m_6")
                포스매출 = st.number_input("포스매출", value=m_포스매출, step=10000, format="%d", key="m_7")
                기타매출 = st.number_input("기타 (먹깨비 등)", value=m_기타매출, step=10000, format="%d", key="m_8")

            with col2:
                st.markdown("#### 🔹 물류 비용 (물류대+음료/주류/기름)")
                물류대 = st.number_input("물류대", value=m_물류대, step=100000, format="%d", key="m_9")
                기름 = st.number_input("기름", value=m_기름, step=10000, format="%d", key="m_10")
                음료 = st.number_input("음료", value=m_음료, step=10000, format="%d", key="m_11")
                주류 = st.number_input("주류", value=m_주류, step=10000, format="%d", key="m_12")

            with col3:
                st.markdown("#### 🔹 운영 비용 (세무·마케팅 포함)")
                인건비 = st.number_input("인건비", value=m_인건비, step=100000, format="%d", key="m_13")
                월세 = st.number_input("월세", value=m_월세, step=10000, format="%d", key="m_14")
                전기세 = st.number_input("전기세", value=m_전기세, step=10000, format="%d", key="m_15")
                가스비 = st.number_input("가스비", value=m_가스비, step=10000, format="%d", key="m_16")
                수도세 = st.number_input("수도세", value=m_수도세, step=10000, format="%d", key="m_17")
                마케팅비용 = st.number_input("마케팅비용", value=m_마케팅비용, step=10000, format="%d", key="m_18")
                포스이용료 = st.number_input("포스이용료", value=m_포스이용료, step=1000, format="%d", key="m_19")
                부가세 = st.number_input("부가세", value=m_부가세, step=10000, format="%d", key="m_20")
                종소세 = st.number_input("종소세", value=m_종소세, step=10000, format="%d", key="m_21")
                퇴직금세이브 = st.number_input("퇴직금세이브", value=m_퇴직금세이브, step=10000, format="%d", key="m_22")
                기타잡비 = st.number_input("기타 경비", value=m_기타잡비, step=10000, format="%d", key="m_23")

            입금합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타매출
            물류합계 = 물류대 + 기름 + 음료 + 주류
            운영합계 = 인건비 + 월세 + 전기세 + 가스비 + 수도세 + 마케팅비용 + 포스이용료 + 부가세 + 종소세 + 퇴직금세이브 + 기타잡비
            최종금액 = 입금합계 - 물류합계 - 운영합계

            입금비율 = (입금합계 / 월매출 * 100) if 월매출 > 0 else 0.0
            물류비율 = (물류합계 / 월매출 * 100) if 월매출 > 0 else 0.0
            인건비율 = (인건비 / 월매출 * 100) if 월매출 > 0 else 0.0
            운영비율 = (운영합계 / 월매출 * 100) if 월매출 > 0 else 0.0
            수익률 = (최종금액 / 월매출 * 100) if 월매출 > 0 else 0.0

            def calc_pct_mimi(val):
                return (val / 월매출 * 100) if 월매출 > 0 else 0.0

            with results_container_mimi:
                st.markdown(f"### 📊 [{selected_store_mimi}] 매장 시뮬레이션 결과")
                
                html_cards_mimi = f"""
                <div class="card-container">
                    <div class="mimi-card">
                        <div class="card-title">1️⃣ 월 매출액</div>
                        <div class="card-value">{월매출:,.0f} 원</div>
                        <div class="card-percent" style="color:#777; background:#f0f0f0;">(기준금액)</div>
                    </div>
                    <div class="mimi-card">
                        <div class="card-title">2️⃣ 입금 합계</div>
                        <div class="card-value">{입금합계:,.0f} 원</div>
                        <div class="card-percent" style="color:#E65100; background-color:#FFF3E0;">매출대비 {입금비율:.1f}%</div>
                    </div>
                    <div class="mimi-card">
                        <div class="card-title">3️⃣ 물류 합계</div>
                        <div class="card-value">{물류합계:,.0f} 원</div>
                        <div class="card-percent" style="color:#E65100; background-color:#FFF3E0;">매출대비 {물류비율:.1f}%</div>
                    </div>
                    <div class="mimi-card">
                        <div class="card-title">4️⃣ 인건비</div>
                        <div class="card-value">{인건비:,.0f} 원</div>
                        <div class="card-percent" style="color:#E65100; background-color:#FFF3E0;">매출대비 {인건비율:.1f}%</div>
                    </div>
                    <div class="mimi-card">
                        <div class="card-title">5️⃣ 운영비 합계</div>
                        <div class="card-value">{운영합계:,.0f} 원</div>
                        <div class="card-percent" style="color:#E65100; background-color:#FFF3E0;">매출대비 {운영비율:.1f}%</div>
                    </div>
                    <div class="mimi-card-final">
                        <div class="card-title">🍲 최종 순수익</div>
                        <div class="card-value">{최종금액:,.0f} 원</div>
                        <div class="card-percent">매출대비 {수익률:.1f}%</div>
                    </div>
                </div>
                
                <div class="mimi-formula-box">
                    💡 계산식 : [ 입금 {입금합계:,.0f}원 ] - [ 물류 {물류합계:,.0f}원 ] - [ 운영비 {운영합계:,.0f}원 ] = <span style="color:#E65100;">최종 순수익 {최종금액:,.0f}원</span>
                </div>
                """
                st.markdown(html_cards_mimi, unsafe_allow_html=True)

                # 세부 내역 표
                st.markdown("#### 📋 세부항목별 금액 및 매출 대비 비율(%)")
                d_col1, d_col2, d_col3 = st.columns(3)

                with d_col1:
                    st.markdown("**💳 입금 세부 내역**")
                    df_income_m = pd.DataFrame([
                        {"항목": "배민", "금액(원)": f"{배민:,.0f}", "매출대비(%)": f"{calc_pct_mimi(배민):.1f}%"},
                        {"항목": "요기요", "금액(원)": f"{요기요:,.0f}", "매출대비(%)": f"{calc_pct_mimi(요기요):.1f}%"},
                        {"항목": "쿠팡이츠", "금액(원)": f"{쿠팡이츠:,.0f}", "매출대비(%)": f"{calc_pct_mimi(쿠팡이츠):.1f}%"},
                        {"항목": "땡겨요", "금액(원)": f"{땡겨요:,.0f}", "매출대비(%)": f"{calc_pct_mimi(땡겨요):.1f}%"},
                        {"항목": "위메프오", "금액(원)": f"{위메프오:,.0f}", "매출대비(%)": f"{calc_pct_mimi(위메프오):.1f}%"},
                        {"항목": "포스매출", "금액(원)": f"{포스매출:,.0f}", "매출대비(%)": f"{calc_pct_mimi(포스매출):.1f}%"},
                        {"항목": "기타매출", "금액(원)": f"{기타매출:,.0f}", "매출대비(%)": f"{calc_pct_mimi(기타매출):.1f}%"},
                    ])
                    st.dataframe(df_income_m, hide_index=True, use_container_width=True)

                with d_col2:
                    st.markdown("**🚚 물류 세부 내역**")
                    df_supply_m = pd.DataFrame([
                        {"항목": "물류대", "금액(원)": f"{물류대:,.0f}", "매출대비(%)": f"{calc_pct_mimi(물류대):.1f}%"},
                        {"항목": "기름", "금액(원)": f"{기름:,.0f}", "매출대비(%)": f"{calc_pct_mimi(기름):.1f}%"},
                        {"항목": "음료", "금액(원)": f"{음료:,.0f}", "매출대비(%)": f"{calc_pct_mimi(음료):.1f}%"},
                        {"항목": "주류", "금액(원)": f"{주류:,.0f}", "매출대비(%)": f"{calc_pct_mimi(주류):.1f}%"},
                    ])
                    st.dataframe(df_supply_m, hide_index=True, use_container_width=True)

                with d_col3:
                    st.markdown("**🏢 운영비 세부 내역**")
                    df_oper_m = pd.DataFrame([
                        {"항목": "인건비", "금액(원)": f"{인건비:,.0f}", "매출대비(%)": f"{calc_pct_mimi(인건비):.1f}%"},
                        {"항목": "월세", "금액(원)": f"{월세:,.0f}", "매출대비(%)": f"{calc_pct_mimi(월세):.1f}%"},
                        {"항목": "전기세", "금액(원)": f"{전기세:,.0f}", "매출대비(%)": f"{calc_pct_mimi(전기세):.1f}%"},
                        {"항목": "가스비", "금액(원)": f"{가스비:,.0f}", "매출대비(%)": f"{calc_pct_mimi(가스비):.1f}%"},
                        {"항목": "수도세", "금액(원)": f"{수도세:,.0f}", "매출대비(%)": f"{calc_pct_mimi(수도세):.1f}%"},
                        {"항목": "마케팅비용", "금액(원)": f"{마케팅비용:,.0f}", "매출대비(%)": f"{calc_pct_mimi(마케팅비용):.1f}%"},
                        {"항목": "포스이용료", "금액(원)": f"{포스이용료:,.0f}", "매출대비(%)": f"{calc_pct_mimi(포스이용료):.1f}%"},
                        {"항목": "부가세", "금액(원)": f"{부가세:,.0f}", "매출대비(%)": f"{calc_pct_mimi(부가세):.1f}%"},
                        {"항목": "종소세", "금액(원)": f"{종소세:,.0f}", "매출대비(%)": f"{calc_pct_mimi(종소세):.1f}%"},
                        {"항목": "퇴직금세이브", "금액(원)": f"{퇴직금세이브:,.0f}", "매출대비(%)": f"{calc_pct_mimi(퇴직금세이브):.1f}%"},
                        {"항목": "기타잡비", "금액(원)": f"{기타잡비:,.0f}", "매출대비(%)": f"{calc_pct_mimi(기타잡비):.1f}%"},
                    ])
                    st.dataframe(df_oper_m, hide_index=True, use_container_width=True)

                st.divider()

                # 그래프
                st.markdown("#### 📈 물류 및 운영비 세부 항목 분석 그래프")
                g_col1, g_col2 = st.columns(2)

                with g_col1:
                    st.markdown("**1. 물류 세부 항목 매출 대비 비율 (%)**")
                    sup_dict_m = {"물류대": calc_pct_mimi(물류대), "기름": calc_pct_mimi(기름), "음료": calc_pct_mimi(음료), "주류": calc_pct_mimi(주류)}
                    fig_sup_m = go.Figure(data=[go.Bar(x=list(sup_dict_m.keys()), y=list(sup_dict_m.values()), text=[f"{v:.1f}%<br>({amt:,.0f}원)" for v, amt in zip(sup_dict_m.values(), [물류대, 기름, 음료, 주류])], textposition='outside', marker_color="#F57C00")])
                    fig_sup_m.update_layout(xaxis=dict(tickfont=dict(size=14)), yaxis=dict(title="비율 (%)"), height=390, margin=dict(l=20, r=20, t=30, b=40), plot_bgcolor="rgba(245,245,245,0.5)")
                    st.plotly_chart(fig_sup_m, use_container_width=True)

                with g_col2:
                    st.markdown("**2. 운영비 세부 항목 매출 대비 비율 (%)**")
                    op_dict_m = {"인건비": calc_pct_mimi(인건비), "월세": calc_pct_mimi(월세), "전기세": calc_pct_mimi(전기세), "가스비": calc_pct_mimi(가스비), "수도세": calc_pct_mimi(수도세), "마케팅비용": calc_pct_mimi(마케팅비용), "포스이용료": calc_pct_mimi(포스이용료), "부가세": calc_pct_mimi(부가세), "종소세": calc_pct_mimi(종소세), "퇴직금세이브": calc_pct_mimi(퇴직금세이브), "기타잡비": calc_pct_mimi(기타잡비)}
                    sorted_op_m = sorted(op_dict_m.items(), key=lambda x: x[1], reverse=True)
                    op_l_m, op_v_m = [x[0] for x in sorted_op_m], [x[1] for x in sorted_op_m]
                    op_amt_map_m = {"인건비": 인건비, "월세": 월세, "전기세": 전기세, "가스비": 가스비, "수도세": 수도세, "마케팅비용": 마케팅비용, "포스이용료": 포스이용료, "부가세": 부가세, "종소세": 종소세, "퇴직금세이브": 퇴직금세이브, "기타잡비": 기타잡비}
                    op_amts_m = [op_amt_map_m[k] for k in op_l_m]
                    
                    fig_op_m = go.Figure(data=[go.Bar(x=op_l_m, y=op_v_m, text=[f"{v:.1f}%<br>({amt:,.0f}원)" for v, amt in zip(op_v_m, op_amts_m)], textposition='outside', marker_color="#E65100")])
                    fig_op_m.update_layout(xaxis=dict(tickangle=-30, tickfont=dict(size=13)), yaxis=dict(title="비율 (%)"), height=390, margin=dict(l=20, r=20, t=30, b=60), plot_bgcolor="rgba(245,245,245,0.5)")
                    st.plotly_chart(fig_op_m, use_container_width=True)
    else:
        st.info("👆 위 영역에 미미순두부 손익 엑셀 파일을 업로드해주세요.")