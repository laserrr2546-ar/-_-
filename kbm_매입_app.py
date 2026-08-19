import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

st.set_page_config(
    page_title="본사 매입현황 대시보드",
    layout="wide"
)

st.title("🛒 본사 품목별 매입현황 대시보드")
st.caption("※ 매입단가 및 매입금을 기준으로 본사의 지출 및 입고 내역을 분석합니다.")

# -------------------
# 다운로드 폴더 자동 감지 (매입현황 파일)
# -------------------
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
FILE_PATTERN = "*매입매출현황(본사)*.xlsx"  

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
    "원본 엑셀 파일(품목별 매입매출현황_본사)을 업로드해주세요",
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
            
        # 이번 파일은 위에 2줄의 불필요한 헤더가 있으므로 header=2 로 지정하여 3번째 줄부터 읽음
        df = pd.read_excel(file_source, header=2)
        
        required_cols = ["제조사", "품목", "입고", "매입단가", "매입금"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"다음 필수 컬럼을 찾지 못했습니다 : {missing}")
            st.stop()

        # 숫자 데이터 전처리 (콤마 제거 및 숫자로 변환)
        num_cols = ['입고', '매입단가', '매입금']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # '매입금'이 0보다 큰(실제 매입이 발생한) 데이터만 추출
        purchase_df = df[df['매입금'] > 0].copy()

        # 결측치(NaN) 처리
        purchase_df['제조사'] = purchase_df['제조사'].fillna('미상(기타)')
        purchase_df['품목'] = purchase_df['품목'].fillna('알 수 없음')
        purchase_df['규격'] = purchase_df['규격'].fillna('-')

        # -------------------
        # 전체 요약 지표 (KPI)
        # -------------------
        st.markdown("---")
        total_purchase = purchase_df["매입금"].sum()
        total_qty = purchase_df["입고"].sum()
        
        # 총 매입금을 총 입고수량으로 나눈 대략적인 '평균 매입단가'
        avg_unit_price = (total_purchase / total_qty) if total_qty > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("총 매입금 (지출 총액)", f"{total_purchase:,.0f} 원")
        col2.metric("총 매입(입고) 수량", f"{total_qty:,.0f} 개/단위")
        col3.metric("평균 매입단가", f"{avg_unit_price:,.0f} 원")

        st.markdown("---")

        # -------------------
        # 1. 제조사별 매입금 TOP 10 (바 차트)
        # -------------------
        st.header("🏢 주요 매입처(제조사) TOP 10")
        
        maker_sales = purchase_df.groupby('제조사', dropna=False)[['매입금', '입고']].sum().reset_index()
        maker_sales = maker_sales.sort_values('매입금', ascending=False).head(10)
        
        fig_maker = px.bar(
            maker_sales, 
            x="제조사", 
            y="매입금", 
            title="상위 10개 제조사별 총 매입금액",
            text_auto='.2s'
        )
        fig_maker.update_traces(marker_color="#FF6B6B") # 지출(매입)을 의미하는 붉은색 계열 적용
        fig_maker.update_layout(yaxis_tickformat=",.0f")
        st.plotly_chart(fig_maker, use_container_width=True)

        # -------------------
        # 2. 품목별 매입금 TOP 10 (표 - 그래프 없음)
        # -------------------
        st.header("🥇 매입 비중이 가장 높은 품목 TOP 10")
        st.caption("※ 매입 금액을 기준으로 지출이 가장 큰 10개 품목입니다.")
        
        item_sales = purchase_df.groupby(['품목', '규격'], dropna=False).agg({
            '입고': 'sum',
            '매입단가': 'mean', # 단가의 경우 평균값으로 표시
            '매입금': 'sum'
        }).reset_index()
        
        item_sales.rename(columns={'입고': '총 입고수량', '매입단가': '평균 매입단가'}, inplace=True)
        item_sales = item_sales.sort_values(by='매입금', ascending=False).head(10)
        item_sales.insert(0, '순위', range(1, 11)) # 순위 삽입

        st.dataframe(
            item_sales,
            use_container_width=True,
            hide_index=True,
            column_config={
                "순위": st.column_config.NumberColumn("순위", format="%d위"),
                "품목": "품목명",
                "규격": "규격",
                "총 입고수량": st.column_config.NumberColumn("총 입고수량", format="%d"),
                "평균 매입단가": st.column_config.NumberColumn("평균 매입단가", format=WON_FORMAT),
                "매입금": st.column_config.NumberColumn("총 매입금", format=WON_FORMAT)
            }
        )

        st.markdown("---")

        # -------------------
        # 3. 데이터 검색 및 상세 매입 내역 확인
        # -------------------
        st.header("🔍 상세 매입 내역 검색")
        
        col_search1, col_search2 = st.columns(2)
        with col_search1:
            keyword_maker = st.text_input("매입처(제조사) 검색")
        with col_search2:
            keyword_item = st.text_input("품목명 검색")

        # 상세 내역용 데이터 정제
        detail_df = purchase_df[['제조사', '품목', '규격', '입고', '매입단가', '매입금']].copy()
        detail_df.sort_values(by='매입금', ascending=False, inplace=True)
        detail_df.rename(columns={'입고': '입고수량'}, inplace=True)

        if keyword_maker:
            detail_df = detail_df[detail_df['제조사'].str.contains(keyword_maker, case=False, na=False)]
        if keyword_item:
            detail_df = detail_df[detail_df['품목'].str.contains(keyword_item, case=False, na=False)]

        st.dataframe(
            detail_df,
            use_container_width=True,
            height=600,
            hide_index=True,
            column_config={
                "제조사": "매입처",
                "입고수량": st.column_config.NumberColumn("입고수량", format="%d"),
                "매입단가": st.column_config.NumberColumn("매입단가", format=WON_FORMAT),
                "매입금": st.column_config.NumberColumn("총 매입금", format=WON_FORMAT)
            }
        )

    except Exception as e:
        st.error(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")