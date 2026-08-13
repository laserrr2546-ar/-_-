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
FILE_PATTERN = "*기간별_매출분석*.xlsx"  # 파일명 패턴이 바뀌면 이 부분만 수정

# 다운로드 폴더가 실제로 존재하는지 확인 (내 PC에서는 True, 웹 서버에서는 False)
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
# 데이터 처리 로직 (기존과 동일)
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
    # 수도권 = 서울/경기/인천 + 대전/강원/충청 통합
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
        # -------------------
        # 헤더 자동 감지
        # -------------------
        header_row_idx = find_header_row(file_source)
        if hasattr(file_source, "seek"):
            file_source.seek(0)  # 업로드된 파일(스트림)인 경우에만 커서 되돌리기
        df = pd.read_excel(file_source, header=header_row_idx)
        st.success(f"엑셀 로딩 완료 (헤더 인식: {header_row_idx + 1}번째 행)")

        data = df.copy()

        with st.expander("인식된 컬럼 보기"):
            st.write(list(data.columns))

        # -------------------
        # 매장명 컬럼 찾기
        # -------------------
        store_col = None
        for col in data.columns:
            if "매장명" in str(col):
                store_col = col
                break

        if store_col is None:
            st.error("매장명 컬럼을 찾지 못했습니다.")
            st.stop()

        # -------------------
        # 합계 행 등 제거
        # -------------------
        data = data.dropna(subset=[store_col])
        data[store_col] = data[store_col].astype(str).str.strip()
        data = data[~data[store_col].isin(["합계", "소계", "총계", ""])]
        data = data[~data[store_col].str.contains("합계|소계|총계", na=False)]

        # -------------------
        # 필수 컬럼 확인
        # -------------------
        required_cols = ["판매금액", "채널배달료(매출제외)"]
        missing = [c for c in required_cols if c not in data.columns]
        if missing:
            st.error(f"다음 컬럼을 찾지 못했습니다 : {missing}")
            st.stop()

        # -------------------
        # 실제매출 계산
        # -------------------
        data["판매금액"] = pd.to_numeric(data["판매금액"], errors="coerce").fillna(0)
        data["채널배달료(매출제외)"] = pd.to_numeric(data["채널배달료(매출제외)"], errors="coerce").fillna(0)
        data["실제매출"] = data["판매금액"] - data["채널배달료(매출제외)"]

        # -------------------
        # 지역/권역
        # -------------------
        data["지역"] = data[store_col].apply(get_region)
        data["권역"] = data["지역"].apply(get_area)

        # -------------------
        # 총매출
        # -------------------
        total_sales = data["실제매출"].sum()
        st.metric("전국 총매출", f"{total_sales:,.0f} 원")

        # -------------------
        # 매장별 매출 합산
        # -------------------
        store_sales = (
            data.groupby([store_col, "지역", "권역"], as_index=False)["실제매출"]
            .sum()
            .sort_values("실제매출", ascending=False)
        )

        # -------------------
        # TOP10
        # -------------------
        st.header("전국 TOP10 매장")

        top10 = store_sales.head(10)

        st.dataframe(
            top10,
            use_container_width=True,
            column_config={
                "실제매출": st.column_config.NumberColumn("실제매출", format=WON_FORMAT)
            }
        )

        fig_top10 = px.bar(top10, x=store_col, y="실제매출", title="전국 TOP10 매장")
        fig_top10.update_traces(marker_color="green")
        fig_top10.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_top10, use_container_width=True)

        # -------------------
        # 하위 10개 매장
        # -------------------
        st.header("🔴 하위 10개 매장")

        bottom10 = store_sales.tail(10)

        st.dataframe(
            bottom10,
            use_container_width=True,
            column_config={
                "실제매출": st.column_config.NumberColumn("실제매출", format=WON_FORMAT)
            }
        )

        fig_bottom10 = px.bar(bottom10, x=store_col, y="실제매출", title="하위 10개 매장")
        fig_bottom10.update_traces(marker_color="red")
        fig_bottom10.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_bottom10, use_container_width=True)

        # -------------------
        # 권역별 매출
        # -------------------
        st.header("권역별 매출")

        area_sales = (
            data.groupby("권역")["실제매출"].sum().reset_index()
            .sort_values("실제매출", ascending=False)
        )

        # 권역별 지점수 계산 (매장 기준 store_sales에서 카운트)
        area_store_count = (
            store_sales.groupby("권역")[store_col].count()
            .reset_index()
            .rename(columns={store_col: "지점수"})
        )

        area_sales = area_sales.merge(area_store_count, on="권역")

        total_sales_for_pct = area_sales["실제매출"].sum()
        total_store_count = area_sales["지점수"].sum()

        area_sales["지점비율(%)"] = area_sales["지점수"] / total_store_count * 100
        area_sales["매출비율(%)"] = area_sales["실제매출"] / total_sales_for_pct * 100

        area_sales = area_sales[["권역", "지점수", "지점비율(%)", "실제매출", "매출비율(%)"]]

        # 합계 행 추가 (표 전용, 그래프에는 포함하지 않음)
        total_row = pd.DataFrame({
            "권역": ["합계"],
            "지점수": [total_store_count],
            "지점비율(%)": [100.0],
            "실제매출": [total_sales_for_pct],
            "매출비율(%)": [100.0],
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
            })
        )

        st.dataframe(styled_area, use_container_width=True)

        fig_area = px.bar(area_sales, x="권역", y="실제매출", title="권역별 매출")
        fig_area.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_area, use_container_width=True)

        if (area_sales["권역"] == "기타(미분류)").any():
            st.warning("권역 미분류 매장이 있습니다. 아래 '지역 미분류 매장 목록'을 확인해주세요.")

        # -------------------
        # 권역별 매출 비중 (파이차트)
        # -------------------
        st.subheader("권역별 매출 비중")

        fig_pie = px.pie(area_sales, names="권역", values="실제매출", hole=0.4)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

        # -------------------
        # 지역별 매출
        # -------------------
        st.header("지역별 매출")

        region_sales = (
            data.groupby("지역")["실제매출"].sum().reset_index()
            .sort_values("실제매출", ascending=False)
        )

        st.dataframe(
            region_sales,
            use_container_width=True,
            column_config={
                "실제매출": st.column_config.NumberColumn("실제매출", format=WON_FORMAT)
            }
        )

        fig_region = px.bar(region_sales, x="지역", y="실제매출", title="지역별 매출")
        fig_region.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_region, use_container_width=True)

        unclassified = data[data["지역"] == "기타"][store_col].unique()
        if len(unclassified) > 0:
            with st.expander(f"⚠ 지역 미분류 매장 목록 ({len(unclassified)}개)"):
                st.write(list(unclassified))

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

        st.dataframe(
            filtered,
            use_container_width=True,
            height=700,
            column_config={
                "실제매출": st.column_config.NumberColumn("실제매출", format=WON_FORMAT)
            }
        )

    except Exception as e:
        st.error(f"오류 발생 : {e}")
