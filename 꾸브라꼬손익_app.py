import streamlit as st

# 페이지 설정
st.set_page_config(page_title="가맹점 손익 계산기", layout="wide")

st.title("📊 가맹점 손익 계산기")
st.markdown("엑셀의 **'가맹점 손익 시트'** 로직을 바탕으로 구현된 대시보드입니다.")

# 사이드바: 데이터 입력
st.sidebar.header("📝 정보 입력")

매장명 = st.sidebar.text_input("매장명", placeholder="예: 김해 내외점")

st.sidebar.subheader("1. 입금 및 매출 정보")
배민 = st.sidebar.number_input("배민 (입금기준)", value=0, step=10000)
요기요 = st.sidebar.number_input("요기요 (입금기준)", value=0, step=10000)
쿠팡이츠 = st.sidebar.number_input("쿠팡이츠 (입금기준)", value=0, step=10000)
땡겨요 = st.sidebar.number_input("땡겨요 (입금기준)", value=0, step=10000)
위메프오 = st.sidebar.number_input("위메프오 (입금기준)", value=0, step=10000)
포스매출 = st.sidebar.number_input("포스매출", value=0, step=10000)
기타매출 = st.sidebar.number_input("기타 (먹깨비, 울산페달 등)", value=0, step=10000)

월매출 = st.sidebar.number_input("월 매출 (총매출액)", value=0, step=100000)

st.sidebar.subheader("2. 물류비")
물류대 = st.sidebar.number_input("물류대", value=0, step=100000)

st.sidebar.subheader("3. 운영비용 (기타 합계)")
인건비 = st.sidebar.number_input("인건비", value=0, step=100000)
기름 = st.sidebar.number_input("기름", value=0, step=10000)
음료 = st.sidebar.number_input("음료", value=0, step=10000)
주류 = st.sidebar.number_input("주류", value=0, step=10000)
월세 = st.sidebar.number_input("월세", value=0, step=10000)
공과금 = st.sidebar.number_input("공과금", value=0, step=10000)
퀵비 = st.sidebar.number_input("퀵비", value=0, step=10000)
포스이용료 = st.sidebar.number_input("포스이용료", value=0, step=1000)
기타잡비 = st.sidebar.number_input("기타 잡비 (보험/인터넷/정수기 등)", value=0, step=10000)

# ==========================================
# 핵심 계산 로직
# ==========================================
입금합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타매출
운영비용_합계 = 인건비 + 기름 + 음료 + 주류 + 월세 + 공과금 + 퀵비 + 포스이용료 + 기타잡비
차감후_입금액 = 입금합계 - 물류대
최종금액 = 차감후_입금액 - 운영비용_합계

# 비율 계산 (0 나누기 방지)
수익률 = (최종금액 / 입금합계 * 100) if 입금합계 > 0 else 0.0
물류비율 = (물류대 / 월매출 * 100) if 월매출 > 0 else 0.0
인건비율 = (인건비 / 월매출 * 100) if 월매출 > 0 else 0.0

# ==========================================
# 결과 출력 화면
# ==========================================
st.divider()

if 매장명:
    st.subheader(f"🏪 {매장명} 손익 결과")
else:
    st.subheader("🏪 손익 결과")

# 첫 번째 행: 핵심 요약 지표 (입금, 매출, 비용, 최종금액)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("총 입금 합계", f"{입금합계:,.0f} 원")
with col2:
    st.metric("월 매출", f"{월매출:,.0f} 원")
with col3:
    st.metric("총 운영비용", f"{운영비용_합계:,.0f} 원")
with col4:
    st.metric("💰 최종 금액 (순이익)", f"{최종금액:,.0f} 원")

st.divider()

# 두 번째 행: 비율 지표 및 세부 계산 결과
col5, col6 = st.columns(2)

with col5:
    st.markdown("### 📈 핵심 비율")
    st.info(f"**수익률 (입금합계 대비):** {수익률:.2f} %")
    st.warning(f"**물류비율 (월매출 대비):** {물류비율:.2f} %")
    st.error(f"**인건비율 (월매출 대비):** {인건비율:.2f} %")

with col6:
    st.markdown("### 🧮 세부 계산 내역")
    st.text(f"  입금 합계:      {입금합계:,.0f} 원")
    st.text(f"- 물류대:         {물류대:,.0f} 원")
    st.text(f"---------------------------------")
    st.text(f"= 1차 차감액:     {차감후_입금액:,.0f} 원")
    st.text(f"- 운영비용 합계:  {운영비용_합계:,.0f} 원")
    st.text(f"---------------------------------")
    st.text(f"= 최종 순수익:    {최종금액:,.0f} 원")