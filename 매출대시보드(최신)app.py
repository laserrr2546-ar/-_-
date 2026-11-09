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
st.markdown(
    "상단의 **탭 메뉴**를 클릭하여 각 분석 대시보드로 이동할 수 있습니다."
)


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


WON_FORMAT = "₩%,d"

# -------------------------------------------------------------
# [탭 메뉴 구성]
# -------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📊 매출 및 휴무일 대시보드",
    "🍗 메뉴별 판매 분석 대시보드",
    "🛵 채널/플랫폼 심층 분석 대시보드",
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

        data1["판매금액"] = pd.to_numeric(
            data1["판매금액"], errors="coerce"
        ).fillna(0)
        data1["채널배달료(매출제외)"] = pd.to_numeric(
            data1["채널배달료(매출제외)"], errors="coerce"
        ).fillna(0)
        data1["실제매출"] = data1["판매금액"] - data1["채널배달료(매출제외)"]

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

        # 전국 TOP10
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
                    "영업일수", format="%d 일"
                ),
                "휴무일수": st.column_config.NumberColumn(
                    "휴무일수", format="%d 일"
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

        # 휴무일 많은 매장 TOP 10
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
                    "영업일수", format="%d 일"
                ),
                "휴무일수": st.column_config.NumberColumn(
                    "휴무일수", format="%d 일"
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

        # 권역별 매출 (.style 과 부하 제거 -> column_config로 대폭 최적화)
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
                "지점수": st.column_config.NumberColumn(format="%d 개"),
                "지점비율(%)": st.column_config.NumberColumn(format="%.1f %%"),
                "실제매출": st.column_config.NumberColumn(format=WON_FORMAT),
                "매출비율(%)": st.column_config.NumberColumn(format="%.1f %%"),
                "일평균매출": st.column_config.NumberColumn(format=WON_FORMAT),
                "월예상매출": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

        # 매장 검색
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

      # 1. 주력 메뉴 판매 비율
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
                "판매수량": st.column_config.NumberColumn(format="%,d 개"),
                "판매비율(%)": st.column_config.NumberColumn(format="%.1f %%"),
                "실매출액": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

      # 2. 세트 vs 단품
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
                "판매수량": st.column_config.NumberColumn(format="%,d 건"),
                "판매비율(%)": st.column_config.NumberColumn(format="%.1f %%"),
                "실매출액": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

      # 3. 사이드 메뉴
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
                "판매수량": st.column_config.NumberColumn(format="%,d 개"),
                "판매비율(%)": st.column_config.NumberColumn(format="%.1f %%"),
                "실매출액": st.column_config.NumberColumn(format=WON_FORMAT),
            },
        )

      # 4. 뼈 vs 순살
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
                    format="%,d 마리"
                ),
                "판매비율(%)": st.column_config.NumberColumn(format="%.1f %%"),
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

      # 지역별 플랫폼 분석
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

      # 전국 매장 종합 리스트
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
              "포장비율(%)": st.column_config.NumberColumn(format="%.1f %%"),
          },
      )

    except Exception as e:
      st.error(f"탭 3 오류 발생: {e}")