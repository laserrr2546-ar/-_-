import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

st.set_page_config(
    page_title="꾸브라꼬 매출 대시보드",
    layout="wide"
)

st.title("꾸브라꼬 매출 대시보드")

# -------------------
# 내 PC(로컬)인지 웹 서버인지 감지하여 똑똑하게 동작하기
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
# 데이터 처리 로직 
# -------------------
def find_header_row(file, max_scan_rows=5, key_word="매장명"):
    raw = pd.read_excel(file, header=None, nrows=max_scan_rows)
    for i in range(len(raw)):
        row_values = [str(v) for v in raw.iloc[i].tolist()]
        if any(key_word in v for v in row_values):
            return i
    return 0

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

if file_source is not None:
    try:
        header_row_idx = find_header_row(file_source)
        if hasattr(file_source, "seek"):
            file_source.seek(0)
        df = pd.read_excel(file_source, header=header_row_idx)
        
        data = df.copy()

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

        required_cols = ["판매금액", "채널배달료(매출제외)"]
        missing = [c for c in required_cols if c not in data.columns]
        if missing:
            st.error(f"다음 컬럼을 찾지 못했습니다 : {missing}")
            st.stop()

        # -------------------
        # 분석일수 / 영업일 / 휴무일 자동 계산
        # -------------------
        st.markdown("---")
        st.subheader("📅 분석 기간 및 영업일 자동 분석")
        
        has_date_col = "일자" in data.columns
        if has_date_col:
            # 빈 일자 제거 및 전체 기간의 총 날짜 수 계산
            data = data.dropna(subset=["일자"])
            detected_days = data["일자"].nunique()
            st.success(f"엑셀 파일에서 총 **{detected_days}일** 치의 데이터를 자동으로 감지했습니다.")
        else:
            detected_days = 30
            st.warning("'일자' 컬럼이 없어 휴무일을 계산할 수 없습니다. 기본 30일로 세팅됩니다.")
            
        analysis_days = st.number_input(
            "총 분석 기간(일수)을 확인하거나 수정해주세요.", 
            min_value=1, value=int(detected_days), step=1, 
            help="해당 기간을 바탕으로 각 매장의 휴무일(기간 내 매출이 없는 날)이 계산됩니다."
        )
        st.markdown("---")

        data["판매금액"] = pd.to_numeric(data["판매금액"], errors="coerce").fillna(0)
        data["채널배달료(매출제외)"] = pd.to_numeric(data["채널배달료(매출제외)"], errors="coerce").fillna(0)
        data["실제매출"] = data["판매금액"] - data["채널배달료(매출제외)"]

        data["지역"] = data[store_col].apply(get_region)
        data["권역"] = data["지역"].apply(get_area)

        # -------------------
        # 1. 매장별 매출 합산 및 일평균/월예상 계산
        # -------------------
        store_sales = (
            data.groupby([store_col, "지역", "권역"], as_index=False)["실제매출"]
            .sum()
            .sort_values("실제매출", ascending=False)
        )
        
        if has_date_col:
            # 매장별로 실제 매출이 일어난 날(일자)을 카운트하여 '영업일수'로 산정
            open_days_df = data[data["실제매출"] > 0].groupby(store_col)["일자"].nunique().reset_index()
            open_days_df.rename(columns={"일자": "영업일수"}, inplace=True)
            store_sales = store_sales.merge(open_days_df, on=store_col, how="left")
            store_sales["영업일수"] = store_sales["영업일수"].fillna(0)
        else:
            store_sales["영업일수"] = analysis_days
            
        # 휴무일수 = 총 기간 - 영업일수 (마이너스가 나오지 않도록 방어)
        store_sales["휴무일수"] = analysis_days - store_sales["영업일수"]
        store_sales["휴무일수"] = store_sales["휴무일수"].apply(lambda x: x if x > 0 else 0)
        
        # '진짜' 일평균매출 계산 (휴무일을 제외하고 실제로 영업한 날짜로만 나눔)
        store_sales["일평균매출"] = store_sales.apply(
            lambda x: x["실제매출"] / x["영업일수"] if x["영업일수"] > 0 else 0, axis=1
        )
        store_sales["월예상매출"] = store_sales["일평균매출"] * 30

        total_sales = store_sales["실제매출"].sum()
        total_daily_avg = store_sales["일평균매출"].sum()
        total_monthly_est = store_sales["월예상매출"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("전국 총매출", f"{total_sales:,.0f} 원")
        col2.metric("전국 일 평균 매출(영업일 기준 합산)", f"{total_daily_avg:,.0f} 원")
        col3.metric("전국 월 예상 매출", f"{total_monthly_est:,.0f} 원")

        # -------------------
        # 매장 TOP10 / 하위 10
        # -------------------
        st.header("전국 TOP10 매장")
        top10 = store_sales.head(10)
        st.dataframe(
            top10,
            use_container_width=True,
            column_config={
                "실제매출": st.column_config.NumberColumn("실제매출", format=WON_FORMAT),
                "영업일수": st.column_config.NumberColumn("영업일수", format="%d 일"),
                "휴무일수": st.column_config.NumberColumn("휴무일수", format="%d 일"),
                "일평균매출": st.column_config.NumberColumn("일평균매출", format=WON_FORMAT),
                "월예상매출": st.column_config.NumberColumn("월예상매출 (30일 기준)", format=WON_FORMAT)
            }
        )

        st.header("🔴 하위 10개 매장")
        bottom10 = store_sales.tail(10)
        st.dataframe(
            bottom10,
            use_container_width=True,
            column_config={
                "실제매출": st.column_config.NumberColumn("실제매출", format=WON_FORMAT),
                "영업일수": st.column_config.NumberColumn("영업일수", format="%d 일"),
                "휴무일수": st.column_config.NumberColumn("휴무일수", format="%d 일"),
                "일평균매출": st.column_config.NumberColumn("일평균매출", format=WON_FORMAT),
                "월예상매출": st.column_config.NumberColumn("월예상매출 (30일 기준)", format=WON_FORMAT)
            }
        )

        # -------------------
        # 2. 권역별 매출 및 일평균/월예상 계산
        # -------------------
        st.header("권역별 매출")

        area_sales = (
            store_sales.groupby("권역")[["실제매출", "일평균매출", "월예상매출"]].sum().reset_index()
            .sort_values("실제매출", ascending=False)
        )

        area_store_count = (
            store_sales.groupby("권역")[store_col].count()
            .reset_index()
            .rename(columns={store_col: "지점수"})
        )

        area_sales = area_sales.merge(area_store_count, on="권역")

        total_store_count = area_sales["지점수"].sum()
        area_sales["지점비율(%)"] = area_sales["지점수"] / total_store_count * 100
        area_sales["매출비율(%)"] = area_sales["실제매출"] / total_sales * 100

        area_sales = area_sales[["권역", "지점수", "지점비율(%)", "실제매출", "매출비율(%)", "일평균매출", "월예상매출"]]

        total_row = pd.DataFrame({
            "권역": ["합계"],
            "지점수": [total_store_count],
            "지점비율(%)": [100.0],
            "실제매출": [total_sales],
            "매출비율(%)": [100.0],
            "일평균매출": [total_daily_avg],
            "월예상매출": [total_monthly_est]
        })
        area_sales_display = pd.concat([area_sales, total_row], ignore_index=True)

        def highlight_total_row(row):
            if row["권역"] == "합계":
                return ["background-color: #fff3b0; font-weight: bold"] * len(row)
            return [""] * len(row)

        styled_area = (
            area_sales_display.style
            .apply(highlight_total_row, axis=1)
            .format({
                "지점수": "{:,.0f} 개",
                "지점비율(%)": "{:.1f}%",
                "실제매출": "{:,.0f} 원",
                "매출비율(%)": "{:.1f}%",
                "일평균매출": "{:,.0f} 원",
                "월예상매출": "{:,.0f} 원"
            })
        )

        st.dataframe(styled_area, use_container_width=True)

        # -------------------
        # 3. 지역별 매출 및 일평균/월예상 계산
        # -------------------
        st.header("지역별 매출")

        region_sales = (
            store_sales.groupby("지역")[["실제매출", "일평균매출", "월예상매출"]].sum().reset_index()
            .sort_values("실제매출", ascending=False)
        )

        st.dataframe(
            region_sales,
            use_container_width=True,
            column_config={
                "실제매출": st.column_config.NumberColumn("실제매출", format=WON_FORMAT),
                "일평균매출": st.column_config.NumberColumn("일평균매출", format=WON_FORMAT),
                "월예상매출": st.column_config.NumberColumn("월예상매출", format=WON_FORMAT)
            }
        )

        # -------------------
        # 매장 검색
        # -------------------
        st.header("🔍 매장 검색")
        col1, col2 = st.columns(2)

        with col1:
            selected_area = st.selectbox(
                "권역 선택",
                ["전체"] + sorted(store_sales["권역"].unique().tolist())
            )

        with col2:
            keyword = st.text_input("매장명 검색")

        filtered = store_sales.copy()

        if selected_area != "전체":
            filtered = filtered[filtered["권역"] == selected_area]

        if keyword:
            filtered = filtered[
                filtered[store_col].str.contains(keyword, case=False, na=False)
            ]

        # 정렬 기준을 실제매출순으로 지정
        filtered = filtered.sort_values("실제매출", ascending=False)

        st.dataframe(
            filtered,
            use_container_width=True,
            height=700,
            column_config={
                "실제매출": st.column_config.NumberColumn("실제매출", format=WON_FORMAT),
                "영업일수": st.column_config.NumberColumn("영업일수", format="%d 일"),
                "휴무일수": st.column_config.NumberColumn("휴무일수", format="%d 일"),
                "일평균매출": st.column_config.NumberColumn("일평균매출", format=WON_FORMAT),
                "월예상매출": st.column_config.NumberColumn("월예상매출 (30일 기준)", format=WON_FORMAT)
            }
        )

    except Exception as e:
        st.error(f"오류 발생 : {e}")
