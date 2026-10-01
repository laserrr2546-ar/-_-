import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. 페이지 설정 및 커스텀 CSS (꾸브라꼬 브랜드 컬러: Red & White)
# ---------------------------------------------------------
st.set_page_config(page_title="꾸브라꼬 점주 수익 시뮬레이터", layout="wide")

st.markdown("""
    <style>
    .main-title {
        color: #D32F2F;
        text-align: center;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #555555;
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 2px solid #f0f0f0;
        border-top: 5px solid #D32F2F;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #333333;
    }
    .metric-label {
        font-size: 1.1rem;
        color: #666666;
        margin-bottom: 5px;
    }
    .profit-card {
        background-color: #FFF8F8;
        border: 2px solid #D32F2F;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 15px rgba(211, 47, 47, 0.2);
    }
    .profit-value {
        font-size: 2.8rem;
        font-weight: 900;
        color: #D32F2F;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🍗 꾸브라꼬 가맹점 수익 시뮬레이터</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">항목별 입력값을 통해 예상 순수익과 마진율, 세부 내역을 확인하세요.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 사이드바: 입력 항목 (매출/입금, 물류비, 운영비)
# ---------------------------------------------------------
st.sidebar.header("📝 시뮬레이션 데이터 입력")
st.sidebar.caption("※ 단위: 원 (숫자만 입력)")

# [1] 총 매출액 (마진율 계산의 기준)
st.sidebar.subheader("1. 총 매출액")
total_sales = st.sidebar.number_input("해당 월의 총 매출액 (객단가×건수 등)", value=30000000, step=1000000)

# [2] 실제 입금액 (플랫폼별 정산금액 등)
st.sidebar.subheader("2. 플랫폼/채널별 실제 입금액")
baemin = st.sidebar.number_input("배달의민족 입금", value=10000000, step=100000)
yogiyo = st.sidebar.number_input("요기요 입금", value=3000000, step=100000)
coupang = st.sidebar.number_input("쿠팡이츠 입금", value=3000000, step=100000)
others = st.sidebar.number_input("땡겨요/위메프오 등", value=500000, step=100000)
pos_sales = st.sidebar.number_input("포스 매출 (홀/포장 현금+카드)", value=5000000, step=100000)
etc_deposit = st.sidebar.number_input("기타 입금액", value=0, step=100000)

total_deposit = baemin + yogiyo + coupang + others + pos_sales + etc_deposit

# [3] 물류 및 재료비
st.sidebar.subheader("3. 물류 및 재료비")
logistics_fee = st.sidebar.number_input("본사 물류대", value=11000000, step=100000)
oil_fee = st.sidebar.number_input("기름(식용유) 비용", value=800000, step=50000)
beverage_fee = st.sidebar.number_input("음료 사입비용", value=300000, step=50000)
alcohol_fee = st.sidebar.number_input("주류 사입비용", value=200000, step=50000)

total_logistics = logistics_fee + oil_fee + beverage_fee + alcohol_fee

# [4] 매장 운영비 (고정/변동비)
st.sidebar.subheader("4. 매장 운영 및 고정비")
labor_cost = st.sidebar.number_input("인건비 (직원/알바)", value=3500000, step=100000)
rent_cost = st.sidebar.number_input("월세 (임대료)", value=1500000, step=100000)
electricity = st.sidebar.number_input("전기세", value=400000, step=10000)
gas = st.sidebar.number_input("가스비", value=250000, step=10000)
water = st.sidebar.number_input("수도세", value=50000, step=10000)
quick_fee = st.sidebar.number_input("배달대행비 (퀵비 충전 등)", value=1500000, step=100000)
pos_etc = st.sidebar.number_input("포스이용료 및 기타 잡비", value=150000, step=10000)

total_op_cost = labor_cost + rent_cost + electricity + gas + water + quick_fee + pos_etc

# ---------------------------------------------------------
# 3. 데이터 계산 (순수익 및 마진율)
# ---------------------------------------------------------
net_profit = total_deposit - total_logistics - total_op_cost

# 마진율은 '총 매출액' 대비 '순수익'으로 계산 (현재 기준이 되는 데이터나 파일이 첨부되지 않아, 정확한 매장 시뮬레이션 결과를 계산하고 그래프를 시각화해 드리기 어렵습니다. 

분석을 원하시는 엑셀 파일이나 세부 수치를 제공해 주시면, 즉각 데이터를 바탕으로 요청하신 항목을 세부적으로 분류하고 그래프를 작성해 드리겠습니다.

데이터를 올려주시기 전, 일반적인 외식 프랜차이즈 매장의 시뮬레이션을 가정했을 때 각 합계에 들어가는 세부 항목의 예시는 다음과 같습니다.

*   **입금합계 (총 매출)**
    *   배달앱 정산 매출 (배달의민족, 쿠팡이츠, 요기요 등)
    *   홀 결제 (카드 및 현금 매출)
    *   포장(테이크아웃) 결제 매출
*   **물류합계 (식자재 및 부자재 원가)**
    *   본사 물류비 (메인 식재료, 전용 소스류 등)
    *   개별 사입비 (주류, 음료, 신선 야채 등)
    *   부자재비 (포장 용기, 수저, 비닐봉투 등)
*   **운영비합계 (판매비 및 관리비)**
    *   임대료 및 건물 관리비
    *   인건비 (정직원 급여, 파트타임 인건비, 4대보험료)
    *   배달 관련 비용 (앱 중개 수수료, 배달 대행료)
    *   공과금 (전기, 수도, 가스 요금)
    *   기타 유지비 (세무 기장료, 통신비, 방역/보안 유지비 등)

정확한 수치를 제공해 주시면 위 항목별 비중을 한눈에 볼 수 있는 **파이 차트**와, 입금 대비 물류 및 운영비 지출을 직관적으로 비교하는 **막대그래프**를 함께 도출해 드리겠습니다. 

분석할 시뮬레이션 데이터나 파일을 업로드해 주시겠습니까?