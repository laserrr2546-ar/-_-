import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

st.set_page_config(
    page_title="물류센터 매입매출 대시보드",
    layout="wide"
)

st.title("📦 물류센터 매입매출 및 수익 대시보드")

# -------------------
# 내 PC(로컬)인지 웹 서버인지 감지하여 똑똑하게 동작하기
# -------------------
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
# 파일명에 '매입매출현황'이 들어가는 엑셀 파일 찾기
FILE_PATTERN = "*매입매출현황*.xlsx"  

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
WON_FORMAT = "%,d 원"

if file_source is not None:
    try:
        if hasattr(file_source, "seek"):
            file_source.seek(0)
            
        # 데이터 불러오기
        df = pd.read_excel(file_source)
        
        required_cols = ["제조사", "품목", "입고", "매출금", "이익금"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"다음 필수 컬럼을 찾지 못했습니다 : {missing}")
            st.stop()

        # 숫자 데이터 전처리 (콤마 제거)
        num_cols = ['입고', '매출단가', '매출금', '이익금']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # 매출금이 있는 데이터만 필터링
        df_filtered = df[df['매출금'] > 0].copy()

        # -------------------
        # 핵심 로직: 제조사 분리 및 1/n 연산
        # -------------------
        df_filtered['제조사_list'] = df_filtered['제조사'].astype(str).str.split('\n')
        df_filtered['n'] = df_filtered['제조사_list'].apply(len)

        for col in num_cols:
            if col in df_filtered.columns:
                df_filtered[col] = df_filtered[col] / df_filtered['n']

        df_exploded = df_filtered.explode('제조사_list')
        df_exploded['제조사(매입처)'] = df_exploded['제조사_list'].str.strip()

        # 데이터 집계
        report_df = df_exploded.groupby(['제조사(매입처)', '품목', '규격'], dropna=False).agg({
            '입고': 'sum',
            '매출단가': 'sum',
            '매출금': 'sum',
            '이익금': 'sum'
        }).reset_index()

        report_df.rename(columns={'입고': '수량'}, inplace=True)
        report_df.sort_values(by='매출금', ascending=False, inplace=True)

        # -------------------
        # 전체 요약 지표 (KPI)
        # -------------------
        st.markdown("---")
        total_sales = report_df["매출금"].sum()
        total_profit = report_df["이익금"].sum()
        avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("총 매출금 (분석 데이터 기준)", f"{total_sales:,.0f} 원")
        col2.metric("총 이익금", f"{total_profit:,.0f} 원")
        col3.metric("평균 수익률", f"{avg_margin:.1f} %")

        # -------------------
        # 제조사별 매출 TOP 10 차트
        # -------------------
        st.header("🏆 제조사별(매입처) 매출 TOP 10")
        
        maker_sales = report_df.groupby('제조사(매입처)', dropna=False)[['매출금', '이익금']].sum().reset_index()
        maker_sales = maker_sales.sort_values('매출금', ascending=False).head(10)
        
        fig_maker = px.bar(maker_sales, x="제조사(매입처)", y="매출금", title="상위 10개 제조사 매출액 비교")
        fig_maker.update_traces(marker_color="cornflowerblue")
        fig_maker.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_maker, use_container_width=True)

        # -------------------
        # 데이터 검색 및 확인 (기존 표 형태 유지)
        # -------------------
        st.header("🔍 상세 매입/매출 내역 확인")
        
        col_search1, col_search2 = st.columns(2)
        with col_search1:
            keyword_maker = st.text_input("제조사(매입처) 검색")
        with col_search2:
            keyword_item = st.text_input("품목명 검색")

        filtered_df = report_df.copy()
        
        if keyword_maker:
            filtered_df = filtered_df[filtered_df['제조사(매입처)'].str.contains(keyword_maker, case=False, na=False)]
        if keyword_item:
            filtered_df = filtered_df[filtered_df['품목'].str.contains(keyword_item, case=False, na=False)]

        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=600,
            column_config={
                "수량": st.column_config.NumberColumn("수량 (개/단위)", format="%d"),
                "매출단가": st.column_config.NumberColumn("매출단가", format=WON_FORMAT),
                "매출금": st.column_config.NumberColumn("매출금", format=WON_FORMAT),
                "이익금": st.column_config.NumberColumn("이익금", format=WON_FORMAT)
            }
        )

    except Exception as e:
        st.error(f"오류 발생 : {e}")
