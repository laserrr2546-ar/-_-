import glob
import io
import os
import re
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="꾸브라꼬 통합 매출 분석 대시보드", layout="wide")

st.title("🍗 꾸브라꼬 통합 매출 분석 대시보드")
st.markdown("상단의 **탭 메뉴**를 클릭하여 각 분석 대시보드로 이동할 수 있습니다.")


# -------------------------------------------------------------
# [공통 함수 영역] 지역 및 권역 자동 분류
# -------------------------------------------------------------
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
    if token in [
        "서울",
        "경기",
        "인천",
        "부산",
        "울산",
        "대구",
        "광주",
        "대전",
        "강원",
        "제주",
        "충남",
        "충북",
        "경남",
        "경북",
        "전남",
        "전북",
    ]:
      return token
  return "기타"


def get_area(region):
  if region in [
      "서울",
      "경기",
      "인천",
      "대전",
      "강원",
      "충청(충남/충북)",
      "충남",
      "충북",
  ]:
    return "수도권"
  if region in ["부산", "울산", "대구", "경상(경남/경북)", "경남", "경북"]:
    return "영남권"
  if region in ["광주", "전라(전남/전북)", "전남", "전북"]:
    return "호남권"
  if region == "제주":
    return "제주권"
  return "기타(미분류)"


def find_date_column(df):
  candidates = [
      "일자",
      "영업일",
      "날짜",
      "매출일자",
      "기준일자",
      "월",
      "년월",
      "연월",
      "기간",
  ]
  for c in candidates:
    if c in df.columns:
      return c
  for col in df.columns:
    s = str(col).strip()
    if (
        any(k in s for k in ["일자", "날짜", "년월", "연월", "기간"])
        or s == "월"
    ):
      return col

  best_col = None
  best_hits = 0
  for col in df.columns:
    sample = df[col].dropna().astype(str).head(50)
    if sample.empty:
      continue
    hits = sum(
        1
        for v in sample
        if re.search(
            r"(\d{4}[-/.년]\d{1,2}|\d{6,8}|\d{1,2}\s*월|\d{1,2}/\d{1,2}/\d{2,4})",
            v.strip(),
        )
    )
    if hits > best_hits:
      best_hits = hits
      best_col = col
  return best_col if best_hits >= 3 else None


def parse_korean_month_series(series):
  """모든 날짜/월 값을 정렬 가능한 키 (sort_key)와 한글 월 ('10월')로 반환."""
  if pd.api.types.is_datetime64_any_dtype(series):
    dt = pd.to_datetime(series, errors="coerce")

    def _from_dt(d):
      if pd.isna(d):
        return (None, None)
      return (int(d.year) * 100 + int(d.month), f"{int(d.month)}월")

    pairs = dt.apply(_from_dt)
    return pairs.apply(lambda x: x[0]), pairs.apply(lambda x: x[1])

  def _parse_one(val):
    if pd.isna(val):
      return (None, None)
    s = str(val).strip()
    if not s or s in ["합계", "소계", "총계", "nan", "None", "NaT", "일자"]:
      return (None, None)

    m = re.match(r"^(\d{4})\s*[-/.년]\s*(\d{1,2})(?:\s*[-/.월일\s].*)?$", s)
    if m:
      y, mo = int(m.group(1)), int(m.group(2))
      if 1900 <= y <= 2100 and 1 <= mo <= 12:
        return (y * 100 + mo, f"{mo}월")

    m_yy = re.match(r"^(\d{2})\s*[-/.]\s*(\d{1,2})(?:\s*[-/.\s].*)?$", s)
    if m_yy:
      y = 2000 + int(m_yy.group(1))
      mo = int(m_yy.group(2))
      if 1 <= mo <= 12:
        return (y * 100 + mo, f"{mo}월")

    digits = re.sub(r"\D", "", s)
    if len(digits) in (6, 8):
      y, mo = int(digits[:4]), int(digits[4:6])
      if 1900 <= y <= 2100 and 1 <= mo <= 12:
        return (y * 100 + mo, f"{mo}월")

    m_kr = re.match(r"^(\d{1,2})\s*월(?:\s*\d{1,2}\s*일?)?$", s)
    if m_kr:
      mo = int(m_kr.group(1))
      if 1 <= mo <= 12:
        cur_year = datetime.now().year
        return (cur_year * 100 + mo, f"{mo}월")

    dt = pd.to_datetime(s, errors="coerce")
    if pd.notna(dt) and 1900 <= dt.year <= 2100:
      return (int(dt.year) * 100 + int(dt.month), f"{int(dt.month)}월")

    return (None, None)

  pairs = series.apply(_parse_one)
  return pairs.apply(lambda x: x[0]), pairs.apply(lambda x: x[1])


def calc_sales_from_df(df):
  """(판매금액 - 채널배달료) = 매출 계산."""
  sales_col = None
  fee_col = None
  for col in df.columns:
    s = str(col).strip()
    if sales_col is None and "판매금액" in s:
      sales_col = col
    if fee_col is None and "채널배달료" in s:
      fee_col = col

  if sales_col is not None:
    sale_amt = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)
    fee_amt = (
        pd.to_numeric(df[fee_col], errors="coerce").fillna(0)
        if fee_col is not None
        else 0
    )
    return sale_amt - fee_amt, None
  if "실제매출" in df.columns:
    return pd.to_numeric(df["실제매출"], errors="coerce").fillna(0), None
  return None, "매출 계산용 '판매금액' 컬럼을 찾지 못했습니다."


def build_monthly_summary_by_group(
    src_df, group_cols, all_month_keys, key_to_label
):
  """그룹(권역/지역 등)별 월별 매출 및 전월 대비 증감금액/증감률/증가·하락 테이블 생성."""
  piv = (
      src_df.groupby(group_cols + ["월키"])["매출"]
      .sum()
      .unstack(fill_value=0)
      .reindex(columns=all_month_keys, fill_value=0)
  )
  out = piv.reset_index()
  out = out[group_cols + all_month_keys]

  diff_cols = []
  rate_cols = []
  status_cols = []

  for idx in range(1, len(all_month_keys)):
    prev_k = all_month_keys[idx - 1]
    curr_k = all_month_keys[idx]
    curr_label = key_to_label[curr_k]
    prev_label = key_to_label[prev_k]

    d_col = f"{prev_label}→{curr_label} 증감금액"
    r_col = f"{prev_label}→{curr_label} 증감률(%)"
    s_col = f"{prev_label}→{curr_label} 증가/하락"

    out[d_col] = out[curr_k] - out[prev_k]
    out[r_col] = out.apply(
        lambda r: (
            round(((r[curr_k] - r[prev_k]) / r[prev_k]) * 100, 1)
            if r[prev_k] > 0
            else None
        ),
        axis=1,
    )
    out[s_col] = out[d_col].apply(
        lambda d: "증가" if d > 0 else ("하락" if d < 0 else "변동없음")
    )

    diff_cols.append(d_col)
    rate_cols.append(r_col)
    status_cols.append(s_col)

  r_map = {k: f"{key_to_label[k]} 매출" for k in all_month_keys}
  out = out.rename(columns=r_map)
  return out, r_map, diff_cols, rate_cols, status_cols


# -------------------------------------------------------------
# [탭 5 전용 로더] 주차별 / 권역·지역별 / 플랫폼별 분석용
# -------------------------------------------------------------
def parse_week_dt(val):
  if pd.isna(val):
    return None
  if isinstance(val, (datetime, pd.Timestamp)):
    return pd.Timestamp(val)
  s = str(val).strip()
  m = re.search(r"(\d+)\s*월\s*(\d+)\s*일", s)
  if m:
    try:
      return datetime(datetime.now().year, int(m.group(1)), int(m.group(2)))
    except ValueError:
      return None
  dt = pd.to_datetime(s, errors="coerce")
  return dt if pd.notna(dt) else None


@st.cache_data
def load_weekly_store_data(file_bytes):
  raw = pd.read_excel(io.BytesIO(file_bytes), header=None, nrows=5)
  header_row_idx = 0
  for i in range(len(raw)):
    row_values = [str(v) for v in raw.iloc[i].tolist()]
    if any("매장명" in v for v in row_values):
      header_row_idx = i
      break

  df = pd.read_excel(io.BytesIO(file_bytes), header=header_row_idx)
  date_col = find_date_column(df) or "일자"
  store_col = next((c for c in df.columns if "매장명" in str(c)), "매장명")

  data = df[
      ~df[date_col].astype(str).str.contains("합계|소계|총계", na=False)
  ].copy()
  data = data[
      ~data[store_col].astype(str).str.contains("합계|소계|총계", na=False)
  ].copy()
  data[store_col] = data[store_col].astype(str).str.strip()

  data["DT"] = data[date_col].apply(parse_week_dt)
  data = data.dropna(subset=["DT"])

  data["IsoWeek"] = data["DT"].dt.isocalendar().week.astype(int)

  def _week_label(row):
    dt = row["DT"]
    start_of_week = dt - pd.Timedelta(days=dt.weekday())
    end_of_week = start_of_week + pd.Timedelta(days=6)
    return (
        f"W{row['IsoWeek']:02d}"
        f" ({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')})"
    )

  data["주차명"] = data.apply(_week_label, axis=1)

  sales_s, err = calc_sales_from_df(data)
  if err:
    raise ValueError(err)
  data["실매출"] = sales_s
  data["지역"] = data[store_col].apply(get_region)
  data["권역"] = data["지역"].apply(get_area)
  data["_store_col"] = store_col
  data["_date_col"] = date_col
  return data


@st.cache_data
def load_weekly_platform_data(file_bytes):
  df = pd.read_excel(io.BytesIO(file_bytes), header=1)
  data = df[
      ~df["일자"].astype(str).str.contains("합계|소계|총계", na=False)
  ].copy()
  data["DT"] = pd.to_datetime(data["일자"], errors="coerce")
  data = data.dropna(subset=["DT"])

  data["IsoWeek"] = data["DT"].dt.isocalendar().week.astype(int)

  def _week_label(row):
    dt = row["DT"]
    start_of_week = dt - pd.Timedelta(days=dt.weekday())
    end_of_week = start_of_week + pd.Timedelta(days=6)
    return (
        f"W{row['IsoWeek']:02d}"
        f" ({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')})"
    )

  data["주차명"] = data.apply(_week_label, axis=1)
  data["주문건수"] = pd.to_numeric(data["건수"], errors="coerce").fillna(0)
  data["실매출"] = pd.to_numeric(data["실 매출액"], errors="coerce").fillna(0)
  data["주문구분"] = data["주문구분"].fillna("기타").astype(str).str.strip()
  data["주문채널"] = data["주문채널"].fillna("기타").astype(str).str.strip()
  data["주문채널 상세"] = (
      data["주문채널 상세"].fillna("기타").astype(str).str.strip()
  )
  return data


WON_FORMAT = "₩%,d"

# -------------------------------------------------------------
# [탭 메뉴 구성]
# -------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 매출 및 휴무일 대시보드",
    "🍗 메뉴별 판매 분석 대시보드",
    "🛵 채널/플랫폼 심층 분석 대시보드",
    "📈 월별 매출 증감률 추이",
    "📅 주차별·플랫폼별 분석",
])

# =============================================================
# [TAB 1] 매출 대시보드 (속도 최적화 적용)
# =============================================================
with tab1:
  st.header("📊 매장별 매출, 영업일 및 휴무일 분석")

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

  uploaded_file_tab1 = st.file_uploader(
      "분석할 '기간별 매출분석' 엑셀 파일을 업로드해주세요",
      type=["xlsx"],
      key="upload_tab1",
  )

  file_source_tab1 = None
  if uploaded_file_tab1 is not None:
    file_source_tab1 = uploaded_file_tab1
    st.info("업로드하신 파일을 사용합니다.")
  elif auto_file_path is not None:
    file_source_tab1 = auto_file_path
    st.success(
        "내 PC 다운로드 폴더에서 최신 파일을 자동으로 불러왔습니다:"
        f" {os.path.basename(auto_file_path)}"
    )
  else:
    st.warning("위에서 분석할 엑셀 파일을 직접 업로드해주세요.")

  if file_source_tab1 is not None:
    try:

      @st.cache_data
      def load_tab1_data(file_input):
        raw = pd.read_excel(file_input, header=None, nrows=5)
        header_row_idx = 0
        for i in range(len(raw)):
          row_values = [str(v) for v in raw.iloc[i].tolist()]
          if any("매장명" in v for v in row_values):
            header_row_idx = i
            break

        if hasattr(file_input, "seek"):
          file_input.seek(0)
        df = pd.read_excel(file_input, header=header_row_idx)
        return df

      df_tab1 = load_tab1_data(file_source_tab1)
      data1 = df_tab1.copy()

      store_col = None
      for col in data1.columns:
        if "매장명" in str(col):
          store_col = col
          break

      if store_col is None:
        st.error("매장명 컬럼을 찾지 못했습니다.")
      else:
        data1 = data1.dropna(subset=[store_col])
        data1[store_col] = data1[store_col].astype(str).str.strip()
        data1 = data1[~data1[store_col].isin(["합계", "소계", "총계", ""])]
        data1 = data1[~data1[store_col].str.contains("합계|소계|총계", na=False)]

        sales_series1, err1 = calc_sales_from_df(data1)
        if err1:
          st.error(err1)
          st.stop()
        data1["실제매출"] = sales_series1

        data1["지역"] = data1[store_col].apply(get_region)
        data1["권역"] = data1["지역"].apply(get_area)

        st.markdown("---")
        st.subheader("📅 분석 기간 및 영업일 자동 분석")

        has_date_col = "일자" in data1.columns
        if has_date_col:
          data1 = data1.dropna(subset=["일자"])
          detected_days = data1["일자"].nunique()
          st.success(
              f"엑셀 파일에서 총 **{detected_days}일** 치의 데이터를 자동으로"
              " 감지했습니다."
          )
        else:
          detected_days = 30
          st.warning(
              "'일자' 컬럼이 없어 휴무일을 계산할 수 없습니다. 기본 30일로"
              " 세팅됩니다."
          )

        analysis_days = st.number_input(
            "총 분석 기간(일수)을 확인하거나 수정해주세요.",
            min_value=1,
            value=int(detected_days),
            step=1,
            key="num_days_tab1",
        )
        st.markdown("---")

        store_sales = (
            data1.groupby([store_col, "지역", "권역"], as_index=False)["실제매출"]
            .sum()
            .sort_values("실제매출", ascending=False)
        )

        if has_date_col:
          open_days_df = (
              data1[data1["실제매출"] > 0]
              .groupby(store_col)["일자"]
              .nunique()
              .reset_index()
          )
          open_days_df.rename(columns={"일자": "영업일수"}, inplace=True)
          store_sales = store_sales.merge(
              open_days_df, on=store_col, how="left"
          )
          store_sales["영업일수"] = store_sales["영업일수"].fillna(0)
        else:
          store_sales["영업일수"] = analysis_days

        store_sales["휴무일수"] = analysis_days - store_sales["영업일수"]
        store_sales["휴무일수"] = store_sales["휴무일수"].apply(
            lambda x: x if x > 0 else 0
        )

        store_sales["일평균매출"] = store_sales.apply(
            lambda x: x["실제매출"] / x["영업일수"] if x["영업일수"] > 0 else 0,
            axis=1,
        )
        store_sales["월예상매출"] = store_sales["일평균매출"] * 30

        total_sales = store_sales["실제매출"].sum()
        total_daily_avg = store_sales["일평균매출"].sum()
        total_monthly_est = store_sales["월예상매출"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("전국 총매출", f"{total_sales:,.0f} 원")
        col2.metric("전국 일 평균 매출", f"{total_daily_avg:,.0f} 원")
        col3.metric("전국 월 예상 매출", f"{total_monthly_est:,.0f} 원")

        st.header("🏆 전국 TOP10 매장")
        top10 = store_sales.head(10)
        st.dataframe(
            top10,
            use_container_width=True,
            column_config={
                "실제매출": st.column_config.NumberColumn(
                    "실제매출", format=WON_FORMAT
                ),
                "영업일수": st.column_config.NumberColumn(
                    "영업일수", format="%d일"
                ),
                "휴무일수": st.column_config.NumberColumn(
                    "휴무일수", format="%d일"
                ),
                "일평균매출": st.column_config.NumberColumn(
                    "일평균매출", format=WON_FORMAT
                ),
                "월예상매출": st.column_config.NumberColumn(
                    "월예상매출", format=WON_FORMAT
                ),
            },
        )

        fig_top10 = px.bar(
            top10, x=store_col, y="실제매출", title="전국 TOP10 매장 매출액"
        )
        fig_top10.update_traces(marker_color="green")
        st.plotly_chart(fig_top10, use_container_width=True)

        st.header("💤 휴무일 많은 매장 TOP 10")
        top_holiday10 = store_sales.sort_values(
            by=["휴무일수", "실제매출"], ascending=[False, True]
        ).head(10)
        st.dataframe(
            top_holiday10,
            use_container_width=True,
            column_config={
                "실제매출": st.column_config.NumberColumn(
                    "실제매출", format=WON_FORMAT
                ),
                "영업일수": st.column_config.NumberColumn(
                    "영업일수", format="%d일"
                ),
                "휴무일수": st.column_config.NumberColumn(
                    "휴무일수", format="%d일"
                ),
                "일평균매출": st.column_config.NumberColumn(
                    "일평균매출", format=WON_FORMAT
                ),
                "월예상매출": st.column_config.NumberColumn(
                    "월예상매출", format=WON_FORMAT
                ),
            },
        )
        fig_holiday10 = px.bar(
            top_holiday10,
            x=store_col,
            y="휴무일수",
            title="매장별 휴무일수 비교 (일)",
        )
        fig_holiday10.update_traces(marker_color="orange")
        st.plotly_chart(fig_holiday10, use_container_width=True)

        st.header("권역별 매출")
        area_sales = (
            store_sales.groupby("권역")[["실제매출", "일평균매출", "월예상매출"]]
            .sum()
            .reset_index()
            .sort_values("실제매출", ascending=False)
        )
        area_store_count = (
            store_sales.groupby("권역")[store_col]
            .count()
            .reset_index()
            .rename(columns={store_col: "지점수"})
        )
        area_sales = area_sales.merge(area_store_count, on="권역")
        total_store_count = area_sales["지점수"].sum()
        area_sales["지점비율(%)"] = area_sales["지점수"] / total_store_count * 100
        area_sales["매출비율(%)"] = area_sales["실제매출"] / total_sales * 100

        total_row = pd.DataFrame({
            "권역": ["합계"],
            "지점수": [total_store_count],
            "지점비율(%)": [100.0],
            "실제매출": [total_sales],
            "매출비율(%)": [100.0],
            "일평균매출": [total_daily_avg],
            "월예상매출": [total_monthly_est],
        })
        area_sales_display = pd.concat(
            [area_sales, total_row], ignore_index=True
        )

        st.dataframe(
            area_sales_display,
            use_container_width=True,
            column_config={
                "지점수": st.column_config.NumberColumn(format="%d개"),
                "지점비율(%)": st.column_config.NumberColumn(format="%.1f%%"),
                "실제매출": st.column_config.NumberColumn(format=WON_FORMAT),
                "매출비율(%)": st.column_config.NumberColumn(format="%.1f%%"),
                "일평균매출": st.column_config.NumberColumn(format=WON_FORMAT),
                "월예상매출": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

        st.header("🔍 개별 매장 검색")
        sc1, sc2 = st.columns(2)
        with sc1:
          sel_ar = st.selectbox(
              "권역 선택",
              ["전체"] + sorted(store_sales["권역"].unique().tolist()),
              key="tab1_ar",
          )
        with sc2:
          kw = st.text_input("매장명 검색", key="tab1_kw")

        filtered_t1 = store_sales.copy()
        if sel_ar != "전체":
          filtered_t1 = filtered_t1[filtered_t1["권역"] == sel_ar]
        if kw:
          filtered_t1 = filtered_t1[
              filtered_t1[store_col].str.contains(kw, case=False, na=False)
          ]

        st.dataframe(
            filtered_t1.sort_values("실제매출", ascending=False),
            use_container_width=True,
            height=500,
            column_config={
                "실제매출": st.column_config.NumberColumn(format=WON_FORMAT),
                "일평균매출": st.column_config.NumberColumn(format=WON_FORMAT),
                "월예상매출": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

    except Exception as e:
      st.error(f"탭 1 오류 발생: {e}")

# =============================================================
# [TAB 2] 메뉴별 판매 대시보드 (속도 최적화 적용)
# =============================================================
with tab2:
  st.header("🍗 메뉴별 판매 비율 및 선호도 심층 분석")
  st.markdown(
      "주력 메뉴 판매 비중, 세트 vs 단품, 사이드 메뉴, 뼈 vs 순살 선호도를"
      " 분석합니다."
  )


  def get_target_chicken(menu):
    m = str(menu).replace(" ", "").replace("℃", "도")
    if "170도후라이드" in m:
      return "170도후라이드"
    elif "170도양념" in m:
      return "170도양념치킨"
    elif "170도마늘간장" in m:
      return "170도마늘간장치킨"
    elif "170도간장" in m:
      return "170도간장치킨"
    if "저당양념" in m:
      return "저당양념꾸브"
    elif "양념꾸브" in m:
      return "양념꾸브"
    elif "트러플" in m:
      return "트러플꾸브"
    elif "소금꾸브" in m:
      return "소금꾸브"
    elif "로제" in m:
      return "로제꾸브"
    elif "까르보" in m:
      return "까르보꾸브"
    elif "데리꾸브" in m:
      return "데리꾸브"
    return "기타메뉴"


  def get_menu_type(raw_menu):
    m = str(raw_menu)
    m_no_space = m.replace(" ", "")
    if "안함" in m_no_space:
      return "제외(기타)"
    if (
        m.startswith("-")
        or m.startswith("+")
        or "순살추가" in m_no_space
        or "순살변경" in m_no_space
    ):
      if "순살" in m_no_space:
        return (
            "세트순살옵션"
            if ("메뉴1" in m_no_space or "메뉴2" in m_no_space)
            else "단품순살옵션"
        )
      return "제외(기타)"
    if "배달" in m or "포장" in m_no_space or "홀매출" in m_no_space:
      return "제외(기타)"
    if "두마리" in m_no_space and "세트" in m_no_space:
      return "세트"
    if any(
        k in m
        for k in [
            "사리",
            "똥집",
            "치즈볼",
            "음료",
            "콜라",
            "사이다",
            "튀김",
            "밥",
            "햇반",
            "감자",
            "떡",
            "소스",
            "무",
            "우동",
        ]
    ):
      return "사이드"
    return "단품"


  def get_bone_type(raw_menu, menu_type):
    m_no_space = str(raw_menu).replace(" ", "")
    if menu_type in ["세트", "단품"]:
      return "순살" if "순살" in m_no_space else "뼈"
    return "-"


  uploaded_file_tab2 = st.file_uploader(
      "메뉴별 매출분석 엑셀 파일을 업로드해주세요",
      type=["xlsx"],
      key="upload_tab2",
  )

  if uploaded_file_tab2 is not None:
    try:

      @st.cache_data
      def load_tab2_data(file_input):
        return pd.read_excel(file_input, header=1)

      df_tab2 = load_tab2_data(uploaded_file_tab2)
      data2 = df_tab2.dropna(subset=["메뉴명"]).copy()
      data2 = data2[data2["메뉴명"] != "합계"]

      data2["판매수량"] = pd.to_numeric(
          data2["판매수량"], errors="coerce"
      ).fillna(0)
      data2["실매출액"] = pd.to_numeric(
          data2["실매출액"], errors="coerce"
      ).fillna(0)

      data2["주력메뉴분류"] = data2["메뉴명"].apply(get_target_chicken)
      data2["메뉴형태"] = data2["메뉴명"].apply(get_menu_type)
      data2["뼈_순살"] = data2.apply(
          lambda x: get_bone_type(x["메뉴명"], x["메뉴형태"]), axis=1
      )

      st.markdown("---")
      st.subheader("🏆 1. 핵심 주력 메뉴 판매 비율")
      target_data = data2[data2["주력메뉴분류"] != "기타메뉴"]
      target_sales = (
          target_data.groupby("주력메뉴분류")[["판매수량", "실매출액"]]
          .sum()
          .reset_index()
      )
      target_sales = target_sales.sort_values("판매수량", ascending=False)
      target_sales["판매비율(%)"] = (
          target_sales["판매수량"] / target_sales["판매수량"].sum() * 100
      ).round(1)

      c1, c2 = st.columns([1.2, 1])
      with c1:
        fig1 = px.pie(
            target_sales, names="주력메뉴분류", values="판매수량", hole=0.3
        )
        st.plotly_chart(fig1, use_container_width=True)
      with c2:
        st.dataframe(
            target_sales,
            use_container_width=True,
            hide_index=True,
            column_config={
                "판매수량": st.column_config.NumberColumn(format="%,d개"),
                "판매비율(%)": st.column_config.NumberColumn(format="%.1f%%"),
                "실매출액": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

      st.markdown("---")
      st.subheader("🍔 2. 세트(두마리) vs 단품 판매 비율")
      type_data = data2[data2["메뉴형태"].isin(["세트", "단품"])]
      type_sales = (
          type_data.groupby("메뉴형태")[["판매수량", "실매출액"]]
          .sum()
          .reset_index()
      )

      single_opt_rev = data2.loc[
          data2["메뉴형태"] == "단품순살옵션", "실매출액"
      ].sum()
      set_opt_rev = data2.loc[
          data2["메뉴형태"] == "세트순살옵션", "실매출액"
      ].sum()
      type_sales.loc[type_sales["메뉴형태"] == "단품", "실매출액"] += (
          single_opt_rev
      )
      type_sales.loc[type_sales["메뉴형태"] == "세트", "실매출액"] += set_opt_rev
      type_sales["판매비율(%)"] = (
          type_sales["판매수량"] / type_sales["판매수량"].sum() * 100
      ).round(1)

      c3, c4 = st.columns([1.2, 1])
      with c3:
        fig2 = px.pie(type_sales, names="메뉴형태", values="판매수량", hole=0.3)
        st.plotly_chart(fig2, use_container_width=True)
      with c4:
        st.dataframe(
            type_sales,
            use_container_width=True,
            hide_index=True,
            column_config={
                "판매수량": st.column_config.NumberColumn(format="%,d건"),
                "판매비율(%)": st.column_config.NumberColumn(format="%.1f%%"),
                "실매출액": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

      st.markdown("---")
      st.subheader("🍟 3. 사이드 메뉴 판매 비율")
      side_sales = (
          data2[data2["메뉴형태"] == "사이드"]
          .groupby("메뉴명")[["판매수량", "실매출액"]]
          .sum()
          .reset_index()
          .sort_values("판매수량", ascending=False)
      )
      side_sales["판매비율(%)"] = (
          side_sales["판매수량"] / side_sales["판매수량"].sum() * 100
      ).round(1)

      c5, c6 = st.columns([1.2, 1])
      with c5:
        fig3 = px.pie(
            side_sales.head(15), names="메뉴명", values="판매수량", hole=0.3
        )
        st.plotly_chart(fig3, use_container_width=True)
      with c6:
        st.dataframe(
            side_sales,
            use_container_width=True,
            height=400,
            hide_index=True,
            column_config={
                "판매수량": st.column_config.NumberColumn(format="%,d개"),
                "판매비율(%)": st.column_config.NumberColumn(format="%.1f%%"),
                "실매출액": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

      st.markdown("---")
      st.subheader("🦴 4. 뼈 vs 순살 선호도 (마리 수 기준 역산)")
      single_opt_qty = data2.loc[
          data2["메뉴형태"] == "단품순살옵션", "판매수량"
      ].sum()
      set_opt_qty = data2.loc[
          data2["메뉴형태"] == "세트순살옵션", "판매수량"
      ].sum()
      bone_base = (
          data2[data2["뼈_순살"] != "-"]
          .groupby(["메뉴형태", "뼈_순살"])[["판매수량", "실매출액"]]
          .sum()
          .reset_index()
      )

      s_bone_qty = bone_base.loc[
          (bone_base["메뉴형태"] == "단품") & (bone_base["뼈_순살"] == "뼈"),
          "판매수량",
      ].sum()
      s_bone_rev = bone_base.loc[
          (bone_base["메뉴형태"] == "단품") & (bone_base["뼈_순살"] == "뼈"),
          "실매출액",
      ].sum()
      s_boneless_qty = bone_base.loc[
          (bone_base["메뉴형태"] == "단품") & (bone_base["뼈_순살"] == "순살"),
          "판매수량",
      ].sum()
      s_boneless_rev = bone_base.loc[
          (bone_base["메뉴형태"] == "단품") & (bone_base["뼈_순살"] == "순살"),
          "실매출액",
      ].sum()

      set_bone_qty = bone_base.loc[
          (bone_base["메뉴형태"] == "세트") & (bone_base["뼈_순살"] == "뼈"),
          "판매수량",
      ].sum()
      set_bone_rev = bone_base.loc[
          (bone_base["메뉴형태"] == "세트") & (bone_base["뼈_순살"] == "뼈"),
          "실매출액",
      ].sum()
      set_boneless_qty = bone_base.loc[
          (bone_base["메뉴형태"] == "세트") & (bone_base["뼈_순살"] == "순살"),
          "판매수량",
      ].sum()
      set_boneless_rev = bone_base.loc[
          (bone_base["메뉴형태"] == "세트") & (bone_base["뼈_순살"] == "순살"),
          "실매출액",
      ].sum()

      s_bone_avg = s_bone_rev / s_bone_qty if s_bone_qty > 0 else 0
      set_bone_avg_per_piece = (
          (set_bone_rev / set_bone_qty) / 2 if set_bone_qty > 0 else 0
      )

      final_bone_qty = (s_bone_qty - single_opt_qty) + (
          set_bone_qty * 2 - set_opt_qty
      )
      final_bone_rev = (s_bone_rev - single_opt_qty * s_bone_avg) + (
          set_bone_rev - set_opt_qty * set_bone_avg_per_piece
      )
      final_boneless_qty = (s_boneless_qty + single_opt_qty) + (
          set_boneless_qty * 2 + set_opt_qty
      )
      final_boneless_rev = (
          (s_boneless_rev + single_opt_rev + single_opt_qty * s_bone_avg)
          + set_boneless_rev
          + set_opt_rev
          + set_opt_qty * set_bone_avg_per_piece
      )

      final_bone_df = pd.DataFrame({
          "구분": ["뼈", "순살"],
          "판매수량(마리)": [final_bone_qty, final_boneless_qty],
          "실매출액": [final_bone_rev, final_boneless_rev],
      })
      final_bone_df["판매비율(%)"] = (
          final_bone_df["판매수량(마리)"]
          / final_bone_df["판매수량(마리)"].sum()
          * 100
      ).round(1)

      c7, c8 = st.columns([1.2, 1])
      with c7:
        fig4 = px.pie(
            final_bone_df, names="구분", values="판매수량(마리)", hole=0.3
        )
        st.plotly_chart(fig4, use_container_width=True)
      with c8:
        st.dataframe(
            final_bone_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "판매수량(마리)": st.column_config.NumberColumn(
                    format="%,d마리"
                ),
                "판매비율(%)": st.column_config.NumberColumn(format="%.1f%%"),
                "실매출액": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

    except Exception as e:
      st.error(f"탭 2 오류 발생: {e}")

# =============================================================
# [TAB 3] 채널별 매출 대시보드 (속도 최적화 적용)
# =============================================================
with tab3:
  st.header("🛵 매장별 주문경로 및 플랫폼 심층 분석")
  st.markdown("온라인/오프라인 비중, 플랫폼 점유율, 포장 매출 비율을 분석합니다.")

  uploaded_file_tab3 = st.file_uploader(
      "주문경로별 매출분석 엑셀 파일을 업로드해주세요",
      type=["xlsx"],
      key="upload_tab3",
  )

  if uploaded_file_tab3 is not None:
    try:

      @st.cache_data
      def load_tab3_data(file_bytes):
        df = pd.read_excel(io.BytesIO(file_bytes), header=1)
        df = df.rename(
            columns={"건수.3": "포장건수", "실 매출액.3": "포장매출액"}
        )
        data = df.dropna(subset=["매장명", "주문채널", "주문채널 상세"]).copy()
        data = data[data["매장명"] != "합계"]
        data = data[data["주문구분"] != "합계"]

        for col in ["실 매출액", "포장매출액", "건수", "포장건수"]:
          data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)

        data["지역"] = data["매장명"].apply(get_region)
        data["권역"] = data["지역"].apply(get_area)
        return data

      data3 = load_tab3_data(uploaded_file_tab3.getvalue())

      st.markdown("---")
      st.subheader("🔍 매장 종합/개별 집중 분석")

      store_list = sorted(data3["매장명"].unique().tolist())
      selected_store = st.selectbox(
          "매장명을 검색하거나 선택하세요",
          ["전체 매장 요약"] + store_list,
          key="tab3_store_select",
      )

      view_type = st.radio(
          "📊 플랫폼 분석 기준 선택",
          ["주문채널 (대분류)", "주문채널 상세 (소분류)"],
          horizontal=True,
          key="tab3_view_type",
      )
      target_col = "주문채널 상세" if "상세" in view_type else "주문채널"

      f_data = (
          data3.copy()
          if selected_store == "전체 매장 요약"
          else data3[data3["매장명"] == selected_store].copy()
      )

      tot_sales = f_data["실 매출액"].sum()
      on_sales = f_data[f_data["주문구분"] == "온라인"]["실 매출액"].sum()
      off_sales = f_data[f_data["주문구분"] == "오프라인"]["실 매출액"].sum()
      take_sales = f_data["포장매출액"].sum()

      on_rt = (on_sales / tot_sales * 100) if tot_sales > 0 else 0
      off_rt = (off_sales / tot_sales * 100) if tot_sales > 0 else 0
      take_rt = (take_sales / tot_sales * 100) if tot_sales > 0 else 0

      mc1, mc2, mc3, mc4 = st.columns(4)
      mc1.metric("총 실매출액", f"{tot_sales:,.0f} 원")
      mc2.metric("온라인 매출", f"{on_sales:,.0f} 원", f"비중 {on_rt:.1f}%")
      mc3.metric("오프라인 매출", f"{off_sales:,.0f} 원", f"비중 {off_rt:.1f}%")
      mc4.metric("포장 매출액", f"{take_sales:,.0f} 원", f"비중 {take_rt:.1f}%")

      cc1, cc2, cc3 = st.columns(3)
      with cc1:
        df_onoff = pd.DataFrame(
            {"구분": ["온라인", "오프라인"], "매출액": [on_sales, off_sales]}
        )
        st.plotly_chart(
            px.pie(
                df_onoff,
                names="구분",
                values="매출액",
                title="🌐 온라인 vs 오프라인",
                hole=0.3,
            ),
            use_container_width=True,
        )
      with cc2:
        df_take = pd.DataFrame({
            "구분": ["포장 매출", "기타"],
            "매출액": [take_sales, tot_sales - take_sales],
        })
        st.plotly_chart(
            px.pie(
                df_take,
                names="구분",
                values="매출액",
                title="🛍 포장 비율",
                hole=0.3,
            ),
            use_container_width=True,
        )
      with cc3:
        channel_pie = (
            f_data.groupby(target_col)["실 매출액"].sum().reset_index()
        )
        st.plotly_chart(
            px.pie(
                channel_pie,
                names=target_col,
                values="실 매출액",
                title="🛵 플랫폼 점유율",
                hole=0.3,
            ),
            use_container_width=True,
        )

      st.markdown("---")
      st.header("🗺️ 지역별 플랫폼 점유율 분석")
      rc1, rc2 = st.columns(2)
      with rc1:
        sel_reg = st.selectbox(
            "조회할 지역 선택",
            ["(지역을 선택해주세요)"] + sorted(data3["지역"].unique().tolist()),
            key="tab3_reg",
        )
      with rc2:
        reg_view = st.radio(
            "지역 분석 기준",
            ["주문채널 (대분류)", "주문채널 상세 (소분류)"],
            horizontal=True,
            key="tab3_reg_view",
        )

      reg_target = "주문채널 상세" if "상세" in reg_view else "주문채널"
      if sel_reg != "(지역을 선택해주세요)":
        r_data = data3[data3["지역"] == sel_reg].copy()
        if not r_data.empty:
          r_pie = r_data.groupby(reg_target)["실 매출액"].sum().reset_index()
          st.plotly_chart(
              px.pie(
                  r_pie,
                  names=reg_target,
                  values="실 매출액",
                  title=f"📍 [{sel_reg}] 지역 점유율",
                  hole=0.3,
              ),
              use_container_width=True,
          )

      st.markdown("---")
      st.header("📋 전국 매장 종합 리스트")
      agg_tot = (
          data3.groupby(["권역", "지역", "매장명"])[
              ["실 매출액", "포장매출액"]
          ]
          .sum()
          .reset_index()
          .rename(columns={"실 매출액": "총매출액"})
      )
      agg_on = (
          data3[data3["주문구분"] == "온라인"]
          .groupby("매장명")["실 매출액"]
          .sum()
          .reset_index()
          .rename(columns={"실 매출액": "온라인매출"})
      )
      agg_off = (
          data3[data3["주문구분"] == "오프라인"]
          .groupby("매장명")["실 매출액"]
          .sum()
          .reset_index()
          .rename(columns={"실 매출액": "오프라인매출"})
      )

      store_group = (
          agg_tot.merge(agg_on, on="매장명", how="left")
          .merge(agg_off, on="매장명", how="left")
          .fillna(0)
      )
      store_group["포장비율(%)"] = (
          (store_group["포장매출액"] / store_group["총매출액"] * 100)
          .fillna(0)
          .round(1)
      )

      sc1, sc2 = st.columns(2)
      with sc1:
        s_area = st.selectbox(
            "권역 필터",
            ["전체"] + sorted(store_group["권역"].unique().tolist()),
            key="tab3_s_area",
        )
      with sc2:
        s_kw = st.text_input("매장명 검색", key="tab3_s_kw")

      flist = store_group.copy()
      if s_area != "전체":
        flist = flist[flist["권역"] == s_area]
      if s_kw:
        flist = flist[
            flist["매장명"].str.contains(s_kw, case=False, na=False)
        ]

      st.dataframe(
          flist.sort_values("총매출액", ascending=False),
          use_container_width=True,
          hide_index=True,
          column_config={
              "총매출액": st.column_config.NumberColumn(format=WON_FORMAT),
              "온라인매출": st.column_config.NumberColumn(format=WON_FORMAT),
              "오프라인매출": st.column_config.NumberColumn(format=WON_FORMAT),
              "포장매출액": st.column_config.NumberColumn(format=WON_FORMAT),
              "포장비율(%)": st.column_config.NumberColumn(format="%.1f%%"),
          },
      )

    except Exception as e:
      st.error(f"탭 3 오류 발생: {e}")

# =============================================================
# [TAB 4] 월별 매출 증감률 추이
# =============================================================
with tab4:
  st.header("📈 월별 매출 증감률 추이 (증가 / 하락 분석)")
  st.markdown(
      "매출은 **(판매금액 - 채널배달료)**로 계산하며, 월을 한글(예: 5월,"
      " 6월, ..., 10월)로 자동 인식해 순차적으로 표시합니다."
  )

  DOWNLOADS_DIR_T4 = os.path.join(os.path.expanduser("~"), "Downloads")
  FILE_PATTERN_T4 = "*기간별_매출분석*.xlsx"
  auto_file_path_t4 = None
  if os.path.exists(DOWNLOADS_DIR_T4):
    files_t4 = glob.glob(os.path.join(DOWNLOADS_DIR_T4, FILE_PATTERN_T4))
    if files_t4:
      auto_file_path_t4 = max(files_t4, key=os.path.getmtime)

  uploaded_file_tab4 = st.file_uploader(
      "월별 매출 추이를 분석할 '기간별 매출분석' 엑셀 파일을 업로드해주세요",
      type=["xlsx"],
      key="upload_tab4",
  )

  file_source_tab4 = None
  if uploaded_file_tab4 is not None:
    file_source_tab4 = uploaded_file_tab4
    st.info("탭 4에 업로드하신 파일을 사용합니다.")
  elif auto_file_path_t4 is not None:
    file_source_tab4 = auto_file_path_t4
    st.success(
        "내 PC 다운로드 폴더에서 최신 파일을 자동으로 불러왔습니다:"
        f" {os.path.basename(auto_file_path_t4)}"
    )
  else:
    st.warning("위에서 분석할 엑셀 파일을 직접 업로드해주세요.")

  if file_source_tab4 is not None:
    try:

      @st.cache_data
      def load_tab4_data(file_input):
        raw = pd.read_excel(file_input, header=None, nrows=5)
        header_row_idx = 0
        for i in range(len(raw)):
          row_values = [str(v) for v in raw.iloc[i].tolist()]
          if any("매장명" in v for v in row_values):
            header_row_idx = i
            break

        if hasattr(file_input, "seek"):
          file_input.seek(0)
        return pd.read_excel(file_input, header=header_row_idx)

      df_tab4 = load_tab4_data(file_source_tab4)
      data4 = df_tab4.copy()

      store_col4 = None
      for col in data4.columns:
        if "매장명" in str(col):
          store_col4 = col
          break

      date_col4 = find_date_column(data4)

      if store_col4 is None:
        st.error("매장명 컬럼을 찾지 못했습니다.")
      elif date_col4 is None:
        st.warning(
            "업로드된 엑셀 파일에 날짜/월 컬럼('일자', '월', '년월' 등)이 없어"
            " 월별 추이를 계산할 수 없습니다."
        )
      else:
        data4 = data4.dropna(subset=[store_col4, date_col4])
        data4[store_col4] = data4[store_col4].astype(str).str.strip()
        data4 = data4[
            ~data4[store_col4].isin(["합계", "소계", "총계", ""])
        ]
        data4 = data4[
            ~data4[store_col4].str.contains("합계|소계|총계", na=False)
        ]

        ym_keys, kr_months = parse_korean_month_series(data4[date_col4])
        data4["월키"] = ym_keys
        data4["월"] = kr_months
        data4 = data4.dropna(subset=["월키", "월"])
        data4["월키"] = data4["월키"].astype(int)

        sales_series4, err4 = calc_sales_from_df(data4)
        if err4:
          st.error(err4)
          st.stop()
        data4["매출"] = sales_series4

        data4["지역"] = data4[store_col4].apply(get_region)
        data4["권역"] = data4["지역"].apply(get_area)

        month_order_df = (
            data4[["월키", "월"]]
            .drop_duplicates()
            .sort_values("월키", ascending=True)
        )
        all_month_keys = month_order_df["월키"].tolist()
        all_months = month_order_df["월"].tolist()
        key_to_label = dict(zip(all_month_keys, all_months))

        st.markdown("---")
        st.subheader("🗓️ 자동 감지된 월 및 조회 범위 설정")
        st.success(
            f"자동 인식된 월 ({len(all_months)}개월): **{', '.join(all_months)}**"
        )

        fc1, fc2 = st.columns([1.4, 1.6])
        with fc1:
          area_filter_t4 = st.selectbox(
              "권역 필터",
              ["전체"] + sorted(data4["권역"].unique().tolist()),
              key="tab4_area",
          )
        with fc2:
          candidate_stores = (
              data4[data4["권역"] == area_filter_t4][store_col4]
              .unique()
              .tolist()
              if area_filter_t4 != "전체"
              else data4[store_col4].unique().tolist()
          )
          store_options_t4 = ["전체 매장 합계"] + sorted(candidate_stores)
          selected_store_t4 = st.selectbox(
              "매장 선택 (예: 꾸브라꼬 부산 장전직영점)",
              store_options_t4,
              key="tab4_store",
          )

        if selected_store_t4 == "전체 매장 합계":
          base_df = (
              data4[data4["권역"] == area_filter_t4]
              if area_filter_t4 != "전체"
              else data4
          )
        else:
          base_df = data4[data4[store_col4] == selected_store_t4]

        seq_sales = (
            base_df.groupby("월키", as_index=False)["매출"]
            .sum()
            .set_index("월키")
            .reindex(all_month_keys, fill_value=0)
            .reset_index()
            .sort_values("월키", ascending=True)
        )
        seq_sales["월"] = seq_sales["월키"].map(key_to_label)
        seq_sales["전월매출"] = seq_sales["매출"].shift(1)
        seq_sales["증감금액"] = seq_sales["매출"] - seq_sales["전월매출"]
        seq_sales["증감률(%)"] = seq_sales.apply(
            lambda r: (
                ((r["매출"] - r["전월매출"]) / r["전월매출"] * 100)
                if pd.notna(r["전월매출"]) and r["전월매출"] > 0
                else None
            ),
            axis=1,
        )
        seq_sales["증가/하락"] = seq_sales.apply(
            lambda r: (
                "기준월"
                if pd.isna(r["증감금액"])
                else (
                    "증가"
                    if r["증감금액"] > 0
                    else ("하락" if r["증감금액"] < 0 else "변동없음")
                )
            ),
            axis=1,
        )

        st.markdown("---")
        st.subheader(
            f"[{selected_store_t4}] 전월 대비 매출 증감률(%) — 증가 및"
            " 하락률 (순차적)"
        )

        if len(seq_sales) >= 1:
          latest_row = seq_sales.iloc[-1]
          prev_row = seq_sales.iloc[-2] if len(seq_sales) >= 2 else None

          k1, k2, k3 = st.columns(3)
          k1.metric(
              f"{latest_row['월']} 매출",
              f"{latest_row['매출']:,.0f}원",
              (
                  f"{latest_row['증가/하락']} {latest_row['증감률(%)']:+.1f}%"
                  if pd.notna(latest_row["증감률(%)"])
                  else "전월 데이터 없음"
              ),
          )
          if prev_row is not None and pd.notna(latest_row["증감금액"]):
            k2.metric(
                f"전월({prev_row['월']}) 대비 증감금액",
                f"{latest_row['증감금액']:+,.0f}원"
                f" ({latest_row['증가/하락']})",
            )
          else:
            k2.metric("전월 대비 증감금액", "-원")

          max_drop_df = seq_sales.dropna(subset=["증감률(%)"])
          if not max_drop_df.empty:
            worst_row = max_drop_df.loc[max_drop_df["증감률(%)"].idxmin()]
            k3.metric(
                "기간 내 최대 하락 월",
                f"{worst_row['월']}",
                f"하락 {worst_row['증감률(%)']:.1f}%",
                delta_color="inverse",
            )
          else:
            k3.metric("기간 내 최대 하락 월", "-")

        rate_seq_df = seq_sales.dropna(subset=["증감률(%)"]).copy()
        if not rate_seq_df.empty:
          rate_seq_df["구분"] = rate_seq_df["증감률(%)"].apply(
              lambda x: "증가" if x > 0 else ("하락" if x < 0 else "변동없음")
          )
          rate_seq_df["차트_라벨"] = rate_seq_df.apply(
              lambda r: (
                  f"{r['증가/하락']} {r['증감률(%)']:+.1f}% | ₩{r['매출']:,.0f}"
              ),
              axis=1,
          )
          fig_seq_rate = px.bar(
              rate_seq_df,
              x="월",
              y="증감률(%)",
              color="구분",
              color_discrete_map={
                  "증가": "#1B9E77",
                  "하락": "#D95F02",
                  "변동없음": "#7570B3",
              },
              text="차트_라벨",
              hover_data=["매출", "전월매출", "증감금액"],
              title=(
                  f"[{selected_store_t4}] 전월 대비 매출 증감률(%) 및 월별"
                  " 매출 (순차적)"
              ),
          )
          fig_seq_rate.update_traces(
              textposition="outside", cliponaxis=False
          )
          fig_seq_rate.update_xaxes(
              categoryorder="array",
              categoryarray=rate_seq_df["월"].tolist(),
          )
          fig_seq_rate.add_hline(y=0, line_dash="dash", line_color="gray")
          st.plotly_chart(fig_seq_rate, use_container_width=True)

        st.dataframe(
            seq_sales[[
                "월",
                "매출",
                "전월매출",
                "증감금액",
                "증감률(%)",
                "증가/하락",
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "매출": st.column_config.NumberColumn(format=WON_FORMAT),
                "전월매출": st.column_config.NumberColumn(format=WON_FORMAT),
                "증감금액": st.column_config.NumberColumn(format="₩%+,.0f"),
                "증감률(%)": st.column_config.NumberColumn(format="%+.1f%%"),
            },
        )

        # -----------------------------------------------------
        # 매장별 월별 매출 및 전월 대비 증감금액·증감률
        # (전체 / 양수 / 음수 / 권역별 선택 / 지역별 선택 탭)
        # -----------------------------------------------------
        st.markdown("---")
        st.subheader("📋 매장별 월별 매출 및 전월 대비 증감금액·증감률")

        matrix_base = (
            data4[data4["권역"] == area_filter_t4]
            if area_filter_t4 != "전체"
            else data4
        )
        kw_t4 = st.text_input(
            "매장명 검색 (표 필터링)", key="tab4_table_kw"
        )
        if kw_t4:
          matrix_base = matrix_base[
              matrix_base[store_col4].str.contains(kw_t4, case=False, na=False)
          ]

        summary_table, rename_map, diff_col_names, rate_col_names, _ = (
            build_monthly_summary_by_group(
                matrix_base,
                [store_col4, "권역", "지역"],
                all_month_keys,
                key_to_label,
            )
        )

        compare_col_t4 = st.selectbox(
            "비교 기준 월 선택",
            rate_col_names if rate_col_names else diff_col_names,
            index=len(rate_col_names) - 1 if rate_col_names else 0,
            key="tab4_compare_col",
        )

        col_cfg_t4 = {}
        for k in all_month_keys:
          m_col = rename_map[k]
          col_cfg_t4[m_col] = st.column_config.NumberColumn(
              m_col, format=WON_FORMAT
          )
        for d_col in diff_col_names:
          col_cfg_t4[d_col] = st.column_config.NumberColumn(
              d_col, format="₩%+,.0f"
          )
        for r_col in rate_col_names:
          col_cfg_t4[r_col] = st.column_config.NumberColumn(
              r_col, format="%+.1f%%"
          )

        all_tab, pos_tab, neg_tab, area_tab, region_tab = st.tabs([
            "📋 전체 매장",
            "📈 양수 매장 (증가)",
            "📉 음수 매장 (하락)",
            "🗺️ 권역별 선택",
            "📍 지역별 선택",
        ])

        with all_tab:
          all_df = summary_table.sort_values(
              by=compare_col_t4, ascending=False, na_position="last"
          )
          st.caption(f"전체 매장: {len(all_df)}개")
          st.dataframe(
              all_df,
              use_container_width=True,
              hide_index=True,
              height=500,
              column_config=col_cfg_t4,
          )

        with pos_tab:
          pos_df = summary_table[
              summary_table[compare_col_t4].notna()
              & (summary_table[compare_col_t4] > 0)
          ].sort_values(by=compare_col_t4, ascending=False)
          st.caption(f"선택 기준 양수(증가) 매장: {len(pos_df)}개")
          st.dataframe(
              pos_df,
              use_container_width=True,
              hide_index=True,
              height=500,
              column_config=col_cfg_t4,
          )

        with neg_tab:
          neg_df = summary_table[
              summary_table[compare_col_t4].notna()
              & (summary_table[compare_col_t4] < 0)
          ].sort_values(by=compare_col_t4, ascending=True)
          st.caption(f"선택 기준 음수(하락) 매장: {len(neg_df)}개")
          st.dataframe(
              neg_df,
              use_container_width=True,
              hide_index=True,
              height=500,
              column_config=col_cfg_t4,
          )

        with area_tab:
          area_options_tab = ["전체 권역"] + sorted(
              data4["권역"].unique().tolist()
          )
          sel_area_tab = st.selectbox(
              "권역 선택", area_options_tab, key="tab4_inner_area"
          )
          area_src = (
              data4.copy()
              if sel_area_tab == "전체 권역"
              else data4[data4["권역"] == sel_area_tab].copy()
          )

          area_summary, a_rmap, a_dcols, a_rcols, _ = (
              build_monthly_summary_by_group(
                  area_src, ["권역"], all_month_keys, key_to_label
              )
          )
          a_cfg = {}
          for k in all_month_keys:
            a_cfg[a_rmap[k]] = st.column_config.NumberColumn(
                a_rmap[k], format=WON_FORMAT
            )
          for d_col in a_dcols:
            a_cfg[d_col] = st.column_config.NumberColumn(
                d_col, format="₩%+,.0f"
            )
          for r_col in a_rcols:
            a_cfg[r_col] = st.column_config.NumberColumn(
                r_col, format="%+.1f%%"
            )

          st.markdown("##### 권역 월별 합계 및 전월 대비 증감")
          st.dataframe(
              area_summary,
              use_container_width=True,
              hide_index=True,
              column_config=a_cfg,
          )

          st.markdown("##### 해당 권역 매장별 상세")
          area_stores_df = summary_table.copy()
          if sel_area_tab != "전체 권역":
            area_stores_df = area_stores_df[
                area_stores_df["권역"] == sel_area_tab
            ]
          st.dataframe(
              area_stores_df.sort_values(
                  by=compare_col_t4, ascending=False, na_position="last"
              ),
              use_container_width=True,
              hide_index=True,
              height=450,
              column_config=col_cfg_t4,
          )

        with region_tab:
          reg_options_tab = ["전체 지역"] + sorted(
              data4["지역"].unique().tolist()
          )
          sel_reg_tab = st.selectbox(
              "지역 선택", reg_options_tab, key="tab4_inner_region"
          )
          reg_src = (
              data4.copy()
              if sel_reg_tab == "전체 지역"
              else data4[data4["지역"] == sel_reg_tab].copy()
          )

          reg_summary, r_rmap, r_dcols, r_rcols, _ = (
              build_monthly_summary_by_group(
                  reg_src, ["권역", "지역"], all_month_keys, key_to_label
              )
          )
          r_cfg = {}
          for k in all_month_keys:
            r_cfg[r_rmap[k]] = st.column_config.NumberColumn(
                r_rmap[k], format=WON_FORMAT
            )
          for d_col in r_dcols:
            r_cfg[d_col] = st.column_config.NumberColumn(
                d_col, format="₩%+,.0f"
            )
          for r_col in r_rcols:
            r_cfg[r_col] = st.column_config.NumberColumn(
                r_col, format="%+.1f%%"
            )

          st.markdown("##### 지역 월별 합계 및 전월 대비 증감")
          st.dataframe(
              reg_summary,
              use_container_width=True,
              hide_index=True,
              column_config=r_cfg,
          )

          st.markdown("##### 해당 지역 매장별 상세")
          reg_stores_df = summary_table.copy()
          if sel_reg_tab != "전체 지역":
            reg_stores_df = reg_stores_df[
                reg_stores_df["지역"] == sel_reg_tab
            ]
          st.dataframe(
              reg_stores_df.sort_values(
                  by=compare_col_t4, ascending=False, na_position="last"
              ),
              use_container_width=True,
              hide_index=True,
              height=450,
              column_config=col_cfg_t4,
          )

    except Exception as e:
      st.error(f"탭 4 오류 발생: {e}")

# =============================================================
# [TAB 5] 주차별·플랫폼별 분석 (추가 통합 탭)
# =============================================================
with tab5:
  st.header("📅 매장별 / 주차별 / 플랫폼별 매출 분석")
  st.markdown(
      "매출은 **(판매금액 - 채널배달료)**로 계산하며, 주차별 추이 및"
      " 플랫폼(주문경로)별 주차 매출을 함께 분석합니다."
  )

  up_c1, up_c2 = st.columns(2)
  with up_c1:
    w_store_file = st.file_uploader(
        "1. 기간별 매출분석 엑셀 (매장별)",
        type=["xlsx", "xls"],
        key="tab5_store_file",
    )
  with up_c2:
    w_plat_file = st.file_uploader(
        "2. 주문경로별 매출분석 엑셀 (플랫폼별)",
        type=["xlsx", "xls"],
        key="tab5_plat_file",
    )

  if w_store_file is not None or w_plat_file is not None:
    try:
      w_data = (
          load_weekly_store_data(w_store_file.getvalue())
          if w_store_file is not None
          else None
      )
      wp_data = (
          load_weekly_platform_data(w_plat_file.getvalue())
          if w_plat_file is not None
          else None
      )

      all_w_labels = sorted(
          set(w_data["주차명"].unique() if w_data is not None else [])
          | set(wp_data["주차명"].unique() if wp_data is not None else [])
      )

      st.markdown("---")
      fc5_1, fc5_2 = st.columns([1.6, 1.4])
      with fc5_1:
        sel_w_labels = st.multiselect(
            "주차 선택 (공통 적용)",
            options=all_w_labels,
            default=all_w_labels,
            key="tab5_weeks",
        )
      with fc5_2:
        if w_data is not None:
          sel_w_areas = st.multiselect(
              "권역 선택 (매장 분석용)",
              options=sorted(w_data["권역"].unique().tolist()),
              default=sorted(w_data["권역"].unique().tolist()),
              key="tab5_areas",
          )
        else:
          sel_w_areas = []

      fw_data = (
          w_data[
              (w_data["주차명"].isin(sel_w_labels))
              & (w_data["권역"].isin(sel_w_areas))
          ].copy()
          if w_data is not None
          else None
      )
      fwp_data = (
          wp_data[wp_data["주차명"].isin(sel_w_labels)].copy()
          if wp_data is not None
          else None
      )

      w_weeks = (
          sorted(fw_data["IsoWeek"].unique().tolist())
          if fw_data is not None
          else []
      )
      wp_weeks = (
          sorted(fwp_data["IsoWeek"].unique().tolist())
          if fwp_data is not None
          else []
      )

      kpi5_1, kpi5_2, kpi5_3, kpi5_4 = st.columns(4)
      if fw_data is not None:
        w_store_col = fw_data["_store_col"].iloc[0]
        kpi5_1.metric("총 실매출", f"{fw_data['실매출'].sum():,.0f} 원")
        kpi5_2.metric("건당 평균 실매출", f"{fw_data['실매출'].mean():,.0f} 원")
        kpi5_3.metric(
            "운영 매장 수", f"{fw_data[w_store_col].nunique():,} 개"
        )
        kpi5_4.metric("총 매출 건수", f"{len(fw_data):,} 건")
      elif fwp_data is not None:
        p_tot_s = fwp_data["실매출"].sum()
        p_tot_o = fwp_data["주문건수"].sum()
        p_avg_o = p_tot_s / p_tot_o if p_tot_o > 0 else 0
        kpi5_1.metric("플랫폼 총 실매출", f"{p_tot_s:,.0f} 원")
        kpi5_2.metric("주문당 평균 단가", f"{p_avg_o:,.0f} 원")
        kpi5_3.metric(
            "활성 주문채널 수", f"{fwp_data['주문채널'].nunique():,} 개"
        )
        kpi5_4.metric("총 주문 건수", f"{p_tot_o:,.0f} 건")

      st.markdown("---")
      st5_1, st5_2, st5_3, st5_4 = st.tabs([
          "🗓️ 주차별 분석",
          "🗺️ 권역/지역별 분석",
          "📱 플랫폼(주문경로)별 분석",
          "📄 상세 데이터",
      ])

      # --- [탭 5 - 1] 주차별 분석 ---
      with st5_1:
        if fw_data is None:
          st.info(
              "위에서 **[1. 기간별 매출분석 엑셀 (매장별)]**을 업로드하면"
              " 매장 기준 주차별 분석이 표시됩니다."
          )
        else:
          st.subheader("주차별 매출 요약")
          weekly_summary = (
              fw_data.groupby("주차명")["실매출"]
              .agg(["sum", "mean", "count"])
              .reset_index()
          )
          weekly_summary.columns = [
              "주차명",
              "주간 총매출",
              "건당 평균매출",
              "매출 발생 건수",
          ]
          total_w_sum = weekly_summary["주간 총매출"].sum()
          weekly_summary["매출 비중(%)"] = (
              weekly_summary["주간 총매출"] / total_w_sum * 100
              if total_w_sum > 0
              else 0
          )

          st.dataframe(
              weekly_summary,
              use_container_width=True,
              hide_index=True,
              column_config={
                  "주간 총매출": st.column_config.NumberColumn(
                      "주간 총매출", format=WON_FORMAT
                  ),
                  "건당 평균매출": st.column_config.NumberColumn(
                      "건당 평균매출", format=WON_FORMAT
                  ),
                  "매출 발생 건수": st.column_config.NumberColumn(
                      "매출 발생 건수", format="%d건"
                  ),
                  "매출 비중(%)": st.column_config.NumberColumn(
                      "매출 비중(%)", format="%.2f%%"
                  ),
              },
          )

          st.plotly_chart(
              px.bar(
                  weekly_summary,
                  x="주차명",
                  y="주간 총매출",
                  text_auto=",",
                  title="주차별 실매출 비교",
              ),
              use_container_width=True,
          )

          st.subheader("매장별 주차별 매출 비교 및 휴무일 현황")
          w_store_col = fw_data["_store_col"].iloc[0]
          week_days_total = fw_data.groupby("IsoWeek")["DT"].nunique().to_dict()

          if len(w_weeks) == 0:
            st.warning("선택된 데이터가 없습니다.")
          else:
            sales_pivot = fw_data.pivot_table(
                index=[w_store_col, "권역", "지역"],
                columns="IsoWeek",
                values="실매출",
                aggfunc="sum",
                fill_value=0,
            )
            sales_pivot.columns = [
                f"{col}주차 매출" for col in sales_pivot.columns
            ]

            days_pivot = fw_data.pivot_table(
                index=[w_store_col, "권역", "지역"],
                columns="IsoWeek",
                values="DT",
                aggfunc="nunique",
                fill_value=0,
            )

            closed_pivot = pd.DataFrame(index=days_pivot.index)
            for col in days_pivot.columns:
              closed_pivot[f"{col}주차 휴무일"] = (
                  week_days_total[col] - days_pivot[col]
              )

            store_summary = pd.concat(
                [sales_pivot, closed_pivot], axis=1
            ).reset_index()

            if len(w_weeks) >= 2:
              curr_wk = w_weeks[-1]
              prev_wk = w_weeks[-2]
              store_summary["매출 증감액(최근2주)"] = (
                  store_summary[f"{curr_wk}주차 매출"]
                  - store_summary[f"{prev_wk}주차 매출"]
              )
              store_summary = store_summary.sort_values(
                  by=f"{curr_wk}주차 매출", ascending=False
              ).reset_index(drop=True)
            else:
              store_summary = store_summary.sort_values(
                  by=f"{w_weeks[0]}주차 매출", ascending=False
              ).reset_index(drop=True)

            search_q5 = st.text_input(
                "🔍 특정 매장 검색",
                placeholder="조회할 매장명을 입력하세요 (예: 부산 정관점)",
                key="tab5_store_search",
            )
            display_w_df = (
                store_summary[
                    store_summary[w_store_col].str.contains(
                        search_q5, na=False
                    )
                ]
                if search_q5
                else store_summary
            )

            base_w_cols = [w_store_col, "권역", "지역"]
            w_sales_cols = [f"{w}주차 매출" for w in w_weeks]
            w_closed_cols = [f"{w}주차 휴무일" for w in w_weeks]
            final_w_cols = base_w_cols + w_sales_cols
            if len(w_weeks) >= 2:
              final_w_cols.append("매출 증감액(최근2주)")
            final_w_cols += w_closed_cols

            display_w_df = display_w_df[final_w_cols]
            chart_w_df = (
                display_w_df if search_q5 else display_w_df.head(20)
            )

            if len(chart_w_df) > 0 and len(w_weeks) >= 2:
              curr_col = f"{curr_wk}주차 매출"
              prev_col = f"{prev_wk}주차 매출"
              chart_melted = chart_w_df.melt(
                  id_vars=[w_store_col],
                  value_vars=[prev_col, curr_col],
                  var_name="주차",
                  value_name="매출액",
              )
              fig_w_store = px.bar(
                  chart_melted,
                  x="매출액",
                  y=w_store_col,
                  color="주차",
                  barmode="group",
                  orientation="h",
                  title=(
                      "검색된 매장 주간 매출 비교"
                      if search_q5
                      else "상위 20개 매장 주간 매출 비교"
                  ),
              )
              fig_w_store.update_layout(
                  yaxis={"categoryorder": "total ascending"}
              )
              st.plotly_chart(fig_w_store, use_container_width=True)
            elif len(chart_w_df) > 0 and len(w_weeks) == 1:
              col_name = f"{w_weeks[0]}주차 매출"
              fig_w_store = px.bar(
                  chart_w_df,
                  x=col_name,
                  y=w_store_col,
                  orientation="h",
                  title=(
                      "검색된 매장 주간 매출"
                      if search_q5
                      else "상위 20개 매장 주간 매출"
                  ),
              )
              fig_w_store.update_layout(
                  yaxis={"categoryorder": "total ascending"}
              )
              st.plotly_chart(fig_w_store, use_container_width=True)

            w_col_cfg = {}
            for col in w_sales_cols:
              w_col_cfg[col] = st.column_config.NumberColumn(
                  col, format=WON_FORMAT
              )
            if "매출 증감액(최근2주)" in final_w_cols:
              w_col_cfg["매출 증감액(최근2주)"] = st.column_config.NumberColumn(
                  "매출 증감액(최근2주)", format="₩%+,.0f"
              )
            for col in w_closed_cols:
              w_col_cfg[col] = st.column_config.NumberColumn(
                  col, format="%d일"
              )

            st.dataframe(
                display_w_df,
                use_container_width=True,
                hide_index=True,
                column_config=w_col_cfg,
            )

      # --- [탭 5 - 2] 권역/지역별 분석 ---
      with st5_2:
        if fw_data is None:
          st.info(
              "위에서 **[1. 기간별 매출분석 엑셀 (매장별)]**을 업로드해주세요."
          )
        else:
          w_store_col = fw_data["_store_col"].iloc[0]
          st.subheader("권역 및 지역별 실매출 분포")
          sub_w1, sub_w2 = st.tabs(["🗺️ 권역별 분석", "📍 상세지역별 분석"])

          with sub_w1:
            area_summary = (
                fw_data.groupby("권역", as_index=False)
                .agg(
                    총매출=("실매출", "sum"),
                    매장수=(w_store_col, "nunique"),
                )
                .sort_values(by="총매출", ascending=False)
            )
            st.plotly_chart(
                px.pie(
                    area_summary,
                    values="총매출",
                    names="권역",
                    title="권역별 총 실매출 비중",
                    hole=0.4,
                ),
                use_container_width=True,
            )

            st.markdown("#### 📊 권역별 주차별 매출 상세")
            if len(w_weeks) > 0:
              area_sales_pivot = fw_data.pivot_table(
                  index=["권역"],
                  columns="IsoWeek",
                  values="실매출",
                  aggfunc="sum",
                  fill_value=0,
              )
              area_sales_pivot.columns = [
                  f"{col}주차 매출" for col in area_sales_pivot.columns
              ]
              area_detail = pd.merge(
                  area_summary,
                  area_sales_pivot.reset_index(),
                  on=["권역"],
                  how="left",
              )
              if len(w_weeks) >= 2:
                area_detail["매출 증감액(최근2주)"] = (
                    area_detail[f"{w_weeks[-1]}주차 매출"]
                    - area_detail[f"{w_weeks[-2]}주차 매출"]
                )

              area_cfg = {
                  "총매출": st.column_config.NumberColumn(
                      "총매출", format=WON_FORMAT
                  ),
                  "매장수": st.column_config.NumberColumn(
                      "매장수", format="%d개"
                  ),
              }
              for col in area_sales_pivot.columns:
                area_cfg[col] = st.column_config.NumberColumn(
                    col, format=WON_FORMAT
                )
              if "매출 증감액(최근2주)" in area_detail.columns:
                area_cfg["매출 증감액(최근2주)"] = st.column_config.NumberColumn(
                    "매출 증감액(최근2주)", format="₩%+,.0f"
                )
              st.dataframe(
                  area_detail,
                  use_container_width=True,
                  hide_index=True,
                  column_config=area_cfg,
              )

          with sub_w2:
            region_summary = (
                fw_data.groupby(["권역", "지역"], as_index=False)
                .agg(
                    총매출=("실매출", "sum"),
                    매장수=(w_store_col, "nunique"),
                )
                .sort_values(by="총매출", ascending=False)
            )
            st.plotly_chart(
                px.bar(
                    region_summary,
                    x="지역",
                    y="총매출",
                    color="권역",
                    title="상세지역별 총 실매출 현황",
                ),
                use_container_width=True,
            )

            st.markdown("#### 📊 상세지역별 주차별 매출 상세")
            if len(w_weeks) > 0:
              region_sales_pivot = fw_data.pivot_table(
                  index=["권역", "지역"],
                  columns="IsoWeek",
                  values="실매출",
                  aggfunc="sum",
                  fill_value=0,
              )
              region_sales_pivot.columns = [
                  f"{col}주차 매출" for col in region_sales_pivot.columns
              ]
              region_detail = pd.merge(
                  region_summary,
                  region_sales_pivot.reset_index(),
                  on=["권역", "지역"],
                  how="left",
              )
              if len(w_weeks) >= 2:
                region_detail["매출 증감액(최근2주)"] = (
                    region_detail[f"{w_weeks[-1]}주차 매출"]
                    - region_detail[f"{w_weeks[-2]}주차 매출"]
                )

              reg_cfg = {
                  "총매출": st.column_config.NumberColumn(
                      "총매출", format=WON_FORMAT
                  ),
                  "매장수": st.column_config.NumberColumn(
                      "매장수", format="%d개"
                  ),
              }
              for col in region_sales_pivot.columns:
                reg_cfg[col] = st.column_config.NumberColumn(
                    col, format=WON_FORMAT
                )
              if "매출 증감액(최근2주)" in region_detail.columns:
                reg_cfg["매출 증감액(최근2주)"] = st.column_config.NumberColumn(
                    "매출 증감액(최근2주)", format="₩%+,.0f"
                )
              st.dataframe(
                  region_detail,
                  use_container_width=True,
                  hide_index=True,
                  column_config=reg_cfg,
              )

      # --- [탭 5 - 3] 플랫폼(주문경로)별 분석 ---
      with st5_3:
        st.subheader("📱 플랫폼(주문경로) 주차별 실매출 분석")
        if fwp_data is None:
          st.info(
              "위에서 **[2. 주문경로별 매출분석 엑셀 (플랫폼별)]**을"
              " 업로드해주세요."
          )
        elif len(wp_weeks) == 0:
          st.warning("선택된 주차에 해당하는 플랫폼 매출 데이터가 없습니다.")
        else:
          channel_col = st.radio(
              "집계 기준 선택",
              options=["주문채널", "주문채널 상세"],
              horizontal=True,
              key="tab5_plat_channel_col",
          )

          plat_summary = (
              fwp_data.groupby(["주문구분", channel_col], as_index=False)
              .agg(총실매출=("실매출", "sum"), 총주문건수=("주문건수", "sum"))
              .sort_values(by="총실매출", ascending=False)
          )
          total_p_rev = plat_summary["총실매출"].sum()
          plat_summary["매출 비중(%)"] = (
              plat_summary["총실매출"] / total_p_rev * 100
              if total_p_rev > 0
              else 0
          )

          pc1, pc2 = st.columns(2)
          with pc1:
            st.plotly_chart(
                px.pie(
                    plat_summary,
                    values="총실매출",
                    names=channel_col,
                    title=f"{channel_col}별 총 실매출 비중",
                    hole=0.4,
                ),
                use_container_width=True,
            )
          with pc2:
            weekly_plat_chart = (
                fwp_data.groupby(["주차명", channel_col], as_index=False)[
                    "실매출"
                ]
                .sum()
                .sort_values(by=["주차명", "실매출"], ascending=[True, False])
            )
            st.plotly_chart(
                px.bar(
                    weekly_plat_chart,
                    x="주차명",
                    y="실매출",
                    color=channel_col,
                    barmode="group",
                    title=f"주차별 {channel_col} 실매출 비교",
                ),
                use_container_width=True,
            )

          st.markdown(f"#### 📊 {channel_col}별 주차별 매출 상세표")
          plat_pivot = fwp_data.pivot_table(
              index=["주문구분", channel_col],
              columns="IsoWeek",
              values="실매출",
              aggfunc="sum",
              fill_value=0,
          )
          plat_pivot.columns = [
              f"{col}주차 매출" for col in plat_pivot.columns
          ]
          plat_detail = pd.merge(
              plat_summary,
              plat_pivot.reset_index(),
              on=["주문구분", channel_col],
              how="left",
          )
          if len(wp_weeks) >= 2:
            plat_detail["매출 증감액(최근2주)"] = (
                plat_detail[f"{wp_weeks[-1]}주차 매출"]
                - plat_detail[f"{wp_weeks[-2]}주차 매출"]
            )

          plat_cfg = {
              "총실매출": st.column_config.NumberColumn(
                  "총실매출", format=WON_FORMAT
              ),
              "총주문건수": st.column_config.NumberColumn(
                  "총주문건수", format="%d건"
              ),
              "매출 비중(%)": st.column_config.NumberColumn(
                  "매출 비중(%)", format="%.2f%%"
              ),
          }
          for col in plat_pivot.columns:
            plat_cfg[col] = st.column_config.NumberColumn(
                col, format=WON_FORMAT
            )
          if "매출 증감액(최근2주)" in plat_detail.columns:
            plat_cfg["매출 증감액(최근2주)"] = st.column_config.NumberColumn(
                "매출 증감액(최근2주)", format="₩%+,.0f"
            )
          st.dataframe(
              plat_detail,
              use_container_width=True,
              hide_index=True,
              column_config=plat_cfg,
          )

      # --- [탭 5 - 4] 상세 데이터 ---
      with st5_4:
        if fw_data is not None:
          w_store_col = fw_data["_store_col"].iloc[0]
          w_date_col = fw_data["_date_col"].iloc[0]
          st.subheader("전체 매장별 필터링 데이터 목록")
          show_cols = [
              c
              for c in [
                  w_date_col,
                  "주차명",
                  "권역",
                  "지역",
                  w_store_col,
                  "판매금액",
                  "채널배달료(매출제외)",
                  "실매출",
              ]
              if c in fw_data.columns
          ]
          st.dataframe(
              fw_data[show_cols], use_container_width=True, hide_index=True
          )

        if fwp_data is not None:
          st.subheader("전체 플랫폼(주문경로)별 필터링 데이터 목록")
          st.dataframe(
              fwp_data[[
                  "일자",
                  "주차명",
                  "주문구분",
                  "주문채널",
                  "주문채널 상세",
                  "주문건수",
                  "실매출",
              ]],
              use_container_width=True,
              hide_index=True,
          )

    except Exception as e:
      st.error(f"탭 5 오류 발생: {e}")
  else:
    st.info(
        "위에서 분석할 엑셀 파일(.xlsx)을 업로드해주세요. (매장별 파일,"
        " 주문경로별 파일 개별 또는 동시 업로드 가능)"
    )