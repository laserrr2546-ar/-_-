import streamlit as st

# ==========================================
# 1. 페이지 및 기본 설정
# ==========================================
st.set_page_config(page_title="가맹점 손익 계산기", layout="wide")

st.title("📊 가맹점 손익 대시보드")
st.markdown("엑셀 파일 **'가맹점 손익 시트'**의 전체 항목과 로직을 그대로 구현한 웹앱입니다.")
st.caption("※ 수익률은 입금 합계 대비, 물류비율/인건비율은 월 매출 대비로 계산됩니다.")

# ==========================================
# 2. 사이드바: 데이터 입력 (엑셀 컬럼 순서 반영)
# ==========================================
st.sidebar.header("📝 매장 데이터 입력")

# 기본정보
st.sidebar.subheader("[ 기본 정보 ]")
no = st.sidebar.text_input("No.", value="1")
매장명 = st.sidebar.text_input("매장명", placeholder="예: 김해 내외점")

# 매출 (입금 기준)
st.sidebar.subheader("[ 매출 및 입금 정보 ]")
배민 = st.sidebar.number_input("배민 (입금기준)", value=0, step=10000)
요기요 = st.sidebar.number_input("요기요 (입금기준)", value=0, step=10000)
쿠팡이츠 = st.sidebar.number_input("쿠팡이츠 (입금기준)", value=0, step=10000)
땡겨요 = st.sidebar.number_input("땡겨요 (입금기준)", value=0, step=10000)
위메프오 = st.sidebar.number_input("위메프오 (입금기준)", value=0, step=10000)
포스매출 = st.sidebar.number_input("포스매출", value=0, step=10000)
기타입금 = st.sidebar.number_input("기타 (먹깨비, 울산페달, 양산배달)", value=0, step=10000)

월매출 = st.sidebar.number_input("월 매출 (전체 매출액)", value=0, step=100000)

# 물류
st.sidebar.subheader("[ 물류 비용 ]")
물류대 = st.sidebar.number_input("물류대", value=0, step=10000)

# 운영비용
st.sidebar.subheader("[ 운영 비용 ]")
인건비 = st.sidebar.number_input("인건비", value=0, step=10000)
기름 = st.sidebar.number_input("기름", value=0, step=10000)
음료 = st.sidebar.number_input("음료", value=0, step=10000)
주류 = st.sidebar.number_input("주류", value=0, step=10000)
월세 = st.sidebar.number_input("월세", value=0, step=10000)
공과금 = st.sidebar.number_input("공과금", value=0, step=10000)
퀵비 = st.sidebar.number_input("퀵비", value=0, step=10000)
포스이용료 = st.sidebar.number_input("포스이용료", value=0, step=1000)
기타잡비 = st.sidebar.number_input("기타 잡비 (보험·인터넷·정수기 등)", value=0, step=10000)


# ==========================================
# 3. 핵심 로직 계산 (엑셀 수식과 동일)
# ==========================================
# 1) 입금 합계
입금_합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타입금

# 2) 입금 합계현재 엑셀 파일이 첨부되지 않았습니다. 

분석하고자 하는 엑셀 파일을 업로드해 주시면, 해당 시트의 데이터를 바탕으로 원하시는 내용을 모두 추출하고 정리해 드리겠습니다. 데이터를 표 형태로 정리할지, 특정 항목을 요약할지 등 원하시는 결과물의 형태도 함께 알려주시면 더욱 정확하게 맞춰서 작업해 드리겠습니다.