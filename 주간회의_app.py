import streamlit as st
import pandas as pd
import re
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="꾸브라꼬 매출 분석 대시보드", layout="wide")

@st.cache_data
def load_and_process_data(uploaded_file):
    # 엑셀 데이터 로드
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

    # 3. 주차명 라벨링 (예: W39 (09.21~09.27))
    def get_week_label(row):
        dt = row["DT"]
        start_of_week = dt - pd.Timedelta(days=dt.weekday())
        end_of_week = start_of_week + pd.Timedelta(days=6)
        return f"W{row['IsoWeek']:02d} ({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')})"

    data["주차명"] = data.apply(get_week_label, axis=1)

    # 4. 금액 처리 및 실제매출 계산
    data["판매금액_val"] = pd.to_numeric(data["판매금액"], errors="coerce").fillna(0)
    data["배달료_val"] = pd.to_numeric(data["채널배달료(매출제외)"], errors="coerce").fillna(0)
    data["실제매출"] = data["판매금액_val"] - data["배달료_val"]

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
    selected_areas = st.sidebar.multiselect("권역 선택", options=sorted(data["권역"].unique()), default=sorted(data["권역"].unique()))
    
    filtered_data = data[(data["주차명"].isin(selected_weeks)) & (data["권역"].isin(selected_areas))]
    
    # 핵심 지표 KPI
    col1, col2, col3, col4 = st.columns(4)
    total_sales = filtered_data["실제매출"].sum()
    avg_sales = filtered_data["실제매출"].mean()
    total_stores = filtered_data["매장명"].nunique()
    total_records = len(filtered_data)
    
    col1.metric("총 실제매출", f"{total_sales:,.0f} 원")
    col2.metric("일평균 매출", f"{avg_sales:,.0f} 원")
    col3.metric("운영 매장 수", f"{total_stores:,} 개")
    col4.metric("총 매출 건수", f"{total_records:,} 건")
    
    st.markdown("---")
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["🗓️ 주차별 분석", "🏪 매장별 분석", "🗺️ 권역/지역별 분석", "📄 상세 데이터"])
    
    # [탭 1] 주차별 분석
    with tab1:
        st.subheader("주차별 매출 요약")
        weekly_summary = filtered_data.groupby("주차명")["실제매출"].agg(["sum", "mean", "count"]).reset_index()
        weekly_summary.columns = ["주차명", "주간 총매출", "일평균 매출", "매출 발생 건수"]
        
        total_sum = weekly_summary["주간 총매출"].sum()
        weekly_summary["매출 비중(%)"] = (weekly_summary["주간 총매출"] / total_sum * 100) if total_sum > 0 else 0
            
        st.dataframe(weekly_summary.style.format({
            "주간 총매출": "{:,.0f}원",
            "일평균 매출": "{:,.0f}원",
            "매출 발생 건수": "{:,}건",
            "매출 비중(%)": "{:.2f}%"
        }), use_container_width=True)
        
        fig_week = px.bar(weekly_summary, x="주차명", y="주간 총매출", text_auto=",", title="주차별 총매출 비교")
        st.plotly_chart(fig_week, use_container_width=True)
        
    # [탭 2] 매장별 분석
    with tab2:
        st.subheader("매장별 매출 순위 (TOP 20)")
        store_summary = filtered_data.groupby(["매장명", "권역", "지역"], as_index=False).agg(
            총매출=("실제매출", "sum"),
            일평균매출=("실제매출", "mean"),
            영업일수=("DT", "nunique")
        ).sort_values(by="총매출", ascending=False)
        
        top20_stores = store_summary.head(20)
        
        fig_store = px.bar(top20_stores, x="총매출", y="매장명", color="권역", orientation="h", title="상위 20개 매장 매출 현황")
        fig_store.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_store, use_container_width=True)
        
        st.dataframe(store_summary.style.format({
            "총매출": "{:,.0f}원",
            "일평균매출": "{:,.0f}원",
            "영업일수": "{:,}일"
        }), use_container_width=True)

    # [탭 3] 권역/지역별 분석
    with tab3:
        st.subheader("권역 및 지역별 매출 분포")
        col_a, col_b = st.columns(2)
        
        area_summary = filtered_data.groupby("권역", as_index=False).agg(
            총매출=("실제매출", "sum"),
            매장수=("매장명", "nunique")
        ).sort_values(by="총매출", ascending=False)
        
        region_summary = filtered_data.groupby(["권역", "지역"], as_index=False).agg(
            총매출=("실제매출", "sum"),
            매장수=("매장명", "nunique")
        ).sort_values(by="총매출", ascending=False)
        
        with col_a:
            fig_area = px.pie(area_summary, values="총매출", names="권역", title="권역별 매출 비중", hole=0.4)
            st.plotly_chart(fig_area, use_container_width=True)
            
        with col_b:
            fig_region = px.bar(region_summary, x="지역", y="총매출", color="권역", title="지역별 총매출 현황")
            st.plotly_chart(fig_region, use_container_width=True)
            
        st.dataframe(region_summary.style.format({
            "총매출": "{:,.0f}원",
            "매장수": "{:,}개"
        }), use_container_width=True)

    # [탭 4] 상세 데이터
    with tab4:
        st.subheader("전체 필터링 데이터 목록")
        st.dataframe(filtered_data[["일자", "주차명", "권역", "지역", "매장명", "실제매출", "판매금액", "채널배달료(매출제외)"]], use_container_width=True)

else:
    st.info("👈 왼쪽 사이드바에서 엑셀 파일(.xlsx)을 업로드해주세요.")