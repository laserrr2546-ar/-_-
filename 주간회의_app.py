import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import re
from datetime import datetime

st.set_page_config(
    page_title="꾸브라꼬 주간 매출 분석 대시보드 (2026)",
    layout="wide"
)

st.title("📊 꾸브라꼬 주간 매출 분석 대시보드")

# -------------------
# 로컬 파일 감지 및 업로드
# -------------------
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
FILE_PATTERN = "*기간별_매출분석*.xlsx"  

is_local_pc = os.path.exists(DOWNLOADS_DIR)
auto_file_path = None

if is_local_pc:
    def find_latest_downloaded_excel():
        files = glob.glob(os.path.join(DOWNLOADS_DIR, FILE_PATTERN))
        if not files:
            return None
        return max(files, key=os.path.getmtime)
    
    auto_file_path = find_latest_downloaded_excel()

uploaded_file = st.file_uploader(
    "분석할 엑셀 파일을 업로드해주세요 (내 PC에서는 다운로드 폴더 자동 감지)",
    type=["xlsx"]
)

if uploaded_file is not None:
    file_source = uploaded_file
    st.info("업로드하신 파일을 사용합니다.")
elif auto_file_path is not None:
    file_source = auto_file_path
    st.success(f"내 PC 다운로드 폴더에서 최신 파일을 자동으로 불러왔습니다: {os.path.basename(auto_file_path)}")
else:
    file_source = None
    st.warning("위에서 분석할 엑셀 파일을 직접 업로드해주세요.")

# -------------------
# 데이터 처리 함수
# -------------------
def find_header_row(file, max_scan_rows=5, key_word="매장명"):
    raw = pd.read_excel(file, header=None, nrows=max_scan_rows)
    for i in range(len(raw)):
        row_values = [str(v) for v in raw.iloc[i].tolist()]
        if any(key_word in v for v in row_values):
            return i
    return 1

def parse_date_2026(val):
    """'10월04일' 형태의 문자열을 2026년 datetime 객체로 변환"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    m = re.search(r'(\d+)월\s*(\d+)일', s)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
        return datetime(2026, month, day)
    return None

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
    if region in ["서울", "경기", "인천", "대전", "강원", "충청(충남/충북)"]:
        return "수도권"
    if region in ["부산", "울산", "대구", "경상(경남/경북)"]:
        return "영남권"
    if region in ["광주", "전라(전남/전북)"]:
        return "호남권"
    if region == "제주":
        return "제주권"
    return "기타(미분류)"

WON_FORMAT = "%,d 원"

# -------------------
# 메인 분석 로직
# -------------------
if file_source is not None:
    try:
        header_row_idx = find_header_row(file_source)
        if hasattr(file_source, "seek"):
            file_source.seek(0)
        
        df = pd.read_excel(file_source, header=header_row_idx)
        data = df.copy()

        # 1. 매장명 컬럼 처리
        store_col = None
        for col in data.columns:
            if "매장명" in str(col):
                store_col = col
                break

        if store_col is None:
            st.error("매장명 컬럼을 찾지 못했습니다.")
            st.stop()

        data = data.dropna(subset=[store_col])
        data[store_col] = data[store_col].astype(str).str.strip()
        data = data[~data[store_col].isin(["합계", "소계", "총계", ""])]
        data = data[~data[store_col].str.contains("합계|소계|총계", na=False)]

        # 2. 날짜 파싱 및 2026년 주차(월~일) 계산
        if "일자" not in data.columns:
            st.error("'일자' 컬럼이 없어 주차별/일자별 분석을 진행할 수 없습니다.")
            st.stop()

        data = data[~data["일자"].astype(str).str.contains("합계|소계|총계", na=False)]
        data["DT"] = data["일자"].apply(parse_date_2026)
        data = data.dropna(subset=["DT"])

        # 월~일 기준 주차 계산 (ISO 주차)
        data["Year"] = data["DT"].dt.year
        data["IsoWeek"] = data["DT"].dt.isocalendar().week
        data["DayOfWeek"] = data["DT"].dt.strftime("%a") # 요일

        # 주차별 시작일(월) ~ 종료일(일) 계산
        def get_week_label(row):
            dt = row["DT"]
            start_of_week = dt - pd.Timedelta(days=dt.weekday())
            end_of_week = start_of_week + pd.Timedelta(days=6)
            return f"W{row['IsoWeek']:02d} ({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')})"

        data["주차명"] = data.apply(get_week_label, axis=1)

        # 3. 매출 관련 금액 정제
        req_sales = "판매금액" if "판매금액" in data.columns else "실매출액"
        req_fee = "채널배달료(매출제외)" if "채널배달료(매출제외)" in data.columns else None

        data["판매금액_val"] = pd.to_numeric(data[req_sales], errors="coerce").fillna(0)
        if req_fee and req_fee in data.columns:
            data["배달료_val"] = pd.to_numeric(data[req_fee], errors="coerce").fillna(0)
            data["실제매출"] = data["판매금액_val"] - data["배달료_val"]
        else:
            data["실제매출"] = data["판매금액_val"]

        data["지역"] = data[store_col].apply(get_region)
        data["권역"] = data["지역"].apply(get_area)
        data["일자_str"] = data["DT"].dt.strftime("%Y-%m-%d")

        # -------------------
        # 주간회의 탭 구성
        # -------------------
        tab1, tab2, tab3, tab4 = st.tabs(["📌 주간 전체 요약", "🗓️ 주차별/매장별 분석", "📆 일자별(하루하루) 상세", "🏢 권역/지역별 분석"])

        # -------------------
        # TAB 1: 주간 전체 요약
        # -------------------
        with tab1:
            st.subheader("💡 주요 실적 지표")
            total_sales = data["실제매출"].sum()
            total_days = data["DT"].nunique()
            active_stores = data[store_col].nunique()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("분석 기간 총 매출", f"{total_sales:,.0f} 원")
            c2.metric("총 분석 일수", f"{total_days} 일")
            c3.metric("일평균 매출 (전국)", f"{(total_sales/total_days if total_days>0 else 0):,.0f} 원")
            c4.metric("운영 매장 수", f"{active_stores} 개점")

            st.markdown("---")
            st.subheader("📈 주차별 매출 추이")
            weekly_summary = data.groupby(["주차명"], as_index=False)["실제매출"].agg(["sum", "mean", "count"]).reset_index()
            weekly_summary.columns = ["주차명", "주간 총매출", "건당 평균매출", "거래건수"]
            
            fig_week = px.bar(
                weekly_summary, 
                x="주차명", 
                y="주간 총매출", 
                text_auto=",f",
                title="2026년 주차별 매출 현황 (월~일 기준)"
            )
            fig_week.update_traces(marker_color="#2E86C1")
            st.plotly_chart(fig_week, use_container_width=True)

        # -------------------
        # TAB 2: 주차별 / 매장별 분석
        # -------------------
        with tab2:
            st.subheader("🏬 주차별 - 매장별 매출 피벗 테이블")
            
            # 필터
            all_weeks = sorted(data["주차명"].unique())
            selected_week = st.selectbox("분석할 주차 선택", ["전체"] + all_weeks)

            df_week_filtered = data.copy()
            if selected_week != "전체":
                df_week_filtered = df_week_filtered[df_week_filtered["주차명"] == selected_week]

            # 매장별 주차 피벗
            pivot_store_week = pd.pivot_table(
                df_week_filtered,
                index=[store_col, "권역", "지역"],
                columns="주차명",
                values="실제매출",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            # 총매출 컬럼 추가
            week_cols = [c for c in pivot_store_week.columns if c not in [store_col, "권역", "지역"]]
            pivot_store_week["합계 매출"] = pivot_store_week[week_cols].sum(axis=1)
            pivot_store_week = pivot_store_week.sort_values(by="합계 매출", ascending=False)

            st.dataframe(
                pivot_store_week,
                use_container_width=True,
                column_config={
                    col: st.column_config.NumberColumn(col, format=WON_FORMAT) for col in week_cols + ["합계 매출"]
                }
            )

        # -------------------
        # TAB 3: 일자별 (하루하루) 상세
        # -------------------
        with tab3:
            st.subheader("📆 일자별(하루하루) 전체 매출 추이")
            daily_sales = data.groupby(["일자_str", "DayOfWeek"], as_index=False)["실제매출"].sum().sort_values("일자_str")
            
            fig_daily = px.line(
                daily_sales, 
                x="일자_str", 
                y="실제매출", 
                markers=True,
                title="일자별 전체 매출 변동"
            )
            st.plotly_chart(fig_daily, use_container_width=True)

            st.markdown("---")
            st.subheader("📋 매장별 일자별 상세 매출 매트릭스")
            
            # 일자 피벗 테이블
            pivot_daily = pd.pivot_table(
                data,
                index=[store_col, "권역"],
                columns="일자_str",
                values="실제매출",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            daily_cols = [c for c in pivot_daily.columns if c not in [store_col, "권역"]]
            pivot_daily["기간 합계"] = pivot_daily[daily_cols].sum(axis=1)
            pivot_daily = pivot_daily.sort_values(by="기간 합계", ascending=False)

            st.dataframe(
                pivot_daily,
                use_container_width=True,
                column_config={
                    col: st.column_config.NumberColumn(col, format=WON_FORMAT) for col in daily_cols + ["기간 합계"]
                }
            )

        # -------------------
        # TAB 4: 권역/지역별 분석
        # -------------------
        with tab4:
            st.subheader("🌐 권역 및 지역별 매출 분포")
            
            col_area, col_reg = st.columns(2)
            
            with col_area:
                area_df = data.groupby("권역", as_index=False)["실제매출"].sum().sort_values("실제매출", ascending=False)
                fig_area = px.pie(area_df, values="실제매출", names="권역", title="권역별 매출 비중", hole=0.4)
                st.plotly_chart(fig_area, use_container_width=True)

            with col_reg:
                region_df = data.groupby("지역", as_index=False)["실제매출"].sum().sort_values("실제매출", ascending=False)
                fig_region = px.bar(region_df, x="지역", y="실제매출", title="지역별 총 매출")
                fig_region.update_traces(marker_color="#27AE60")
                st.plotly_chart(fig_region, use_container_width=True)

    except Exception as e:
        st.error(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")