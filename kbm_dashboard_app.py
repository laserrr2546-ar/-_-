import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import io

st.set_page_config(
    page_title="물류센터 매입매출 대시보드",
    layout="wide"
)

st.title("📦 물류센터 매입매출 및 수익 대시보드")

# -------------------
# 내 PC(로컬)인지 웹 서버인지 감지하여 똑똑하게 동작하기
# -------------------
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
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
    "원본 엑셀 파일(물류센터 매입매출현황)을 업로드해주세요",
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

def get_summary_item(items):
    """품목명을 'A 외 N건' 형태로 요약하는 함수"""
    unique_items = list(pd.Series(items).dropna().unique())
    if len(unique_items) == 0:
        return ""
    elif len(unique_items) == 1:
        return str(unique_items[0])
    else:
        return f"{unique_items[0]} 外 {len(unique_items)-1}건"

if file_source is not None:
    try:
        if hasattr(file_source, "seek"):
            file_source.seek(0)
            
        df = pd.read_excel(file_source)
        
        required_cols = ["제조사", "품목", "입고", "매입금", "매출금", "이익금"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"다음 필수 컬럼을 찾지 못했습니다 : {missing}")
            st.stop()

        # 숫자 데이터 전처리
        num_cols = ['입고', '매입금', '매출단가', '매출금', '이익금']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # 데이터 필터링 (매출금 또는 매입금이 있는 경우)
        df_filtered = df[(df['매출금'] > 0) | (df['매입금'] > 0)].copy()

        # -------------------
        # 제조사 분리 로직 (동일값 복사 유지)
        # -------------------
        df_filtered['제조사_list'] = df_filtered['제조사'].astype(str).str.split('\n')
        df_exploded = df_filtered.explode('제조사_list')
        df_exploded['제조사(매입처)'] = df_exploded['제조사_list'].str.strip()

        # ==========================================
        # 1. 본사 물류수익보고서 마감 양식 생성 로직
        # ==========================================
        report_summary = df_exploded.groupby('제조사(매입처)', dropna=False).agg(
            품목=('품목', get_summary_item),
            총매입금=('매입금', 'sum'),
            매출수량=('입고', 'sum'),
            총매출금=('매출금', 'sum'),
            매출총이익=('이익금', 'sum')
        ).reset_index()

        # 이익률 계산
        report_summary['당월 이익률(%)'] = (report_summary['매출총이익'] / report_summary['총매출금'] * 100).fillna(0)
        
        # 보기 좋게 컬럼 순서 및 정렬
        report_summary = report_summary[['제조사(매입처)', '품목', '매출수량', '총매입금', '총매출금', '매출총이익', '당월 이익률(%)']]
        report_summary.sort_values(by='총매출금', ascending=False, inplace=True)
        report_summary.rename(columns={'제조사(매입처)': '매입처'}, inplace=True)

        # ==========================================
        # 대시보드 화면 출력
        # ==========================================
        st.markdown("---")
        st.header("📑 본사 물류수익 마감보고서 자동 생성")
        st.caption("※ 제조사별로 요약된 마감 양식입니다. 엑셀로 바로 다운로드하여 사용할 수 있습니다.")

        # 엑셀 다운로드 파일 생성 (BytesIO)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            report_summary.to_excel(writer, index=False, sheet_name='매입처 마감')
        output.seek(0)

        # 다운로드 버튼
        st.download_button(
            label="📥 본사 물류수익보고서 엑셀 다운로드",
            data=output,
            file_name="물류수익마감보고서_가공완료.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 요약표 대시보드에 띄우기
        st.dataframe(
            report_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "매출수량": st.column_config.NumberColumn("매출수량", format="%d"),
                "총매입금": st.column_config.NumberColumn("총매입금", format=WON_FORMAT),
                "총매출금": st.column_config.NumberColumn("총매출금", format=WON_FORMAT),
                "매출총이익": st.column_config.NumberColumn("매출총이익", format=WON_FORMAT),
                "당월 이익률(%)": st.column_config.NumberColumn("당월 이익률", format="%.2f %%")
            }
        )

        # ==========================================
        # 전체 요약 지표 (KPI)
        # ==========================================
        st.markdown("---")
        total_sales = report_summary["총매출금"].sum()
        total_profit = report_summary["매출총이익"].sum()
        avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("총 매출금", f"{total_sales:,.0f} 원")
        col2.metric("총 이익금", f"{total_profit:,.0f} 원")
        col3.metric("평균 이익률", f"{avg_margin:.1f} %")

        # -------------------
        # 차트 및 기존 상세 검색 로직 
        # -------------------
        st.header("🏆 제조사별(매입처) 매출 TOP 10")
        top_makers = report_summary.head(10)
        fig_maker = px.bar(top_makers, x="매입처", y="총매출금", title="상위 10개 제조사 매출액 비교")
        fig_maker.update_traces(marker_color="cornflowerblue")
        fig_maker.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_maker, use_container_width=True)

        # 상세 내역 (기존과 동일하게 품목/규격 단위 확인)
        st.header("🔍 품목 단위 상세 내역 확인")
        detail_df = df_exploded.groupby(['제조사(매입처)', '품목', '규격'], dropna=False).agg({
            '입고': 'sum', '매출단가': 'max', '매출금': 'sum', '이익금': 'sum'
        }).reset_index()
        detail_df.rename(columns={'입고': '수량'}, inplace=True)
        detail_df.sort_values(by='매출금', ascending=False, inplace=True)

        col_search1, col_search2 = st.columns(2)
        with col_search1:
            keyword_maker = st.text_input("매입처 검색")
        with col_search2:
            keyword_item = st.text_input("품목명 검색")

        filtered_df = detail_df.copy()
        if keyword_maker:
            filtered_df = filtered_df[filtered_df['제조사(매입처)'].str.contains(keyword_maker, case=False, na=False)]
        if keyword_item:
            filtered_df = filtered_df[filtered_df['품목'].str.contains(keyword_item, case=False, na=False)]

        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=500,
            column_config={
                "수량": st.column_config.NumberColumn("수량 (개)", format="%d"),
                "매출단가": st.column_config.NumberColumn("매출단가", format=WON_FORMAT),
                "매출금": st.column_config.NumberColumn("매출금", format=WON_FORMAT),
                "이익금": st.column_config.NumberColumn("이익금", format=WON_FORMAT)
            }
        )

    except Exception as e:
        st.error(f"오류 발생 : {e}")
