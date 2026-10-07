import streamlit as st
import pandas as pd
import re
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="꾸브라꼬 매출 분석 대시보드", layout="wide")

@st.cache_data
def load_and_process_data(uploaded_file):
    df = pd.read_excel(uploaded_file, header=1)
    
    # 1. 총계/합계/소계 행 제거
    data = df[~df["일자"].astype(str).str.contains("합계|소계|총계", na=False)].copy()
    
    # 2. 날짜 파싱 (2026년 기준)
    def parse_date(val):
        if pd.isna(val):
            return None
        s = str(val).strip()
        m = re.search(r'(\d+)월\s*(\d+)일', s)
        if m:
            return datetime(2026, int(m.group(1)), int(m.group(2)))
        return None

    data["DT"] = data["일자"].apply(parse_date)
    data = data.dropna(subset=["DT"])

    data["Year"] = data["DT"].dt.year
    data["IsoWeek"] = data["DT"].dt.isocalendar().week

    # 3. 주차명 라벨링
    def get_week_label(row):
        dt = row["DT"]
        start_of_week = dt - pd.Timedelta(days=dt.weekday())
        end_of_week = start_of_week + pd.Timedelta(days=6)
        return f"W{row['IsoWeek']:02d} ({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')})"

    data["주차명"] = data.apply(get_week_label, axis=1)

    # 4. 실매출 계산 = 판매금액 - 채널배달료(매출제외)
    data["판매금액_val"] = pd.to_numeric(data["판매금액"], errors="coerce").fillna(0)
    data["배달료_val"] = pd.to_numeric(data["채널배달료(매출제외)"], errors="coerce").fillna(0)
    data["실매출"] = data["판매금액_val"] - data["배달료_val"]

    # 5. 매장명 기반 지역 및 권역 자동 추출
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
            if token in ["서울", "경기", "인천", "부산", "울산", "대구", "광주", "대전", "강원", "제주", "충남", "충북", "경남", "경북", "전남", "전북"]:
                return token
        return "기타"

    def get_area(region):
        if region in ["서울", "경기", "인천", "대전", "강원", "충청(충남/충북)", "충남", "충북"]:
            return "수도권"
        if region in ["부산", "울산", "대구", "경상(경남/경북)", "경남", "경북"]:
            return "영남권"
        if region in ["광주", "전라(전남/전북)", "전남", "전북"]:
            return "호남권"
        if region == "제주":
            return "제주권"
        return "기타"

    data["지역"] = data["매장명"].apply(get_region)
    data["권역"] = data["지역"].apply(get_area)
    
    return data

# 대시보드 타이틀
st.title("📊 매장별/주차별 매출 분석 대시보드")

# 파일 업로드 컨트롤러
file = st.sidebar.file_uploader("기간별 매출분석 엑셀 파일 업로드", type=["xlsx", "xls"])

if file is not None:
    data = load_and_process_data(file)
    
    # 사이드바 필터
    st.sidebar.header("🔍 필터 옵션")
    selected_weeks = st.sidebar.multiselect("주차 선택", options=sorted(data["주차명"].unique()), default=sorted(data["주차명"].unique()))
    selected_areas = st.sidebar.multiselect("권역 선택