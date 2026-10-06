import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="매장별 플랫폼/채널 매출 분석", layout="wide")
st.title("🛵 매장별 주문경로 및 플랫폼 심층 분석")
st.markdown("전국 매장의 지역/권역별 리스트를 확인하고, **온라인/오프라인 비중, 플랫폼 점유율, 포장 매출 비율**을 한눈에 분석합니다.")

# -------------------
# 권역 및 지역 분류 함수
# -------------------
def get_region(store):
    parts = str(store).split()
    if len(parts) >= 2:
        token = parts[1]
        merged = {
            "경상": "경상(경남/경북)",
            "전라": "전라(전남/전북)",
            "충청": "충청(충남/충북)",
        }
        if token in merged:
            return merged[token]
        if token in ["서울", "경기", "인천", "부산", "울산", "대구", "광주", "대전", "강원", "제주"]:
            return token
    return "기타"

def get_area(region):
    if region in ["서울", "경기", "인천", "대전", "강원", "충청(충남/충북)"]: return "수도권"
    if region in ["부산", "울산", "대구", "경상(경남/경북)"]: return "영남권"
    if region in ["광주", "전라(전남/전북)"]: return "호남권"
    if region == "제주": return "제주권"
    return "기타(미분류)"

# -------------------
# 파일 업로드 및 분석
# -------------------
uploaded_file = st.file_uploader("주문경로별 매출분석(매장별) 엑셀 파일을 업로드해주세요", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 데이터 로드 (헤더는 2번째 줄)
        df = pd.read_excel(uploaded_file, header=1)
        
        # 포장 컬럼 이름 변경
        df = df.rename(columns={'건수.3': '포장건수', '실 매출액.3': '포장매출액'})
        
        # 결측치 및 합계 행 제거 (주문채널 대분류, 소분류 모두 체크)
        data = df.dropna(subset=['매장명', '주문채널', '주문채널 상세']).copy()
        data = data[data['매장명'] != '합계']
        data = data[data['주문구분'] != '합계']
        
        # 숫자형 변환
        for col in ['실 매출액', '포장매출액', '건수', '포장건수']:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            
        data['지역'] = data['매장명'].apply(get_region)
        data['권역'] = data['지역'].apply(get_area)

        # ==========================================
        # 1. 상단: 전체 요약 및 개별 매장 상세 검색
        # ==========================================
        st.markdown("---")
        st.header("🔍 매장 종합/개별 집중 분석")
        
        store_list = sorted(data['매장명'].unique().tolist())
        selected_store = st.selectbox(
            "타이핑하여 매장명을 검색하거나 선택하세요 (기본값: 전체 매장 요약)",
            ["전체 매장 요약"] + store_list
        )
        
        # 조회 기준 선택 스위치