import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import io

st.set_page_config(
    page_title="물류센터 매입/매출 통합 대시보드",
    layout="wide"
)

st.title("📦 물류센터 매입/매출 통합 대시보드")
st.caption("※ 아래 탭(Tab)을 클릭하여 '매출 분석'과 '매입 분석'을 자유롭게 전환할 수 있습니다.")

# -------------------
# 다운로드 폴더 자동 감지
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
    "원본 엑셀 파일(매입매출현황)을 업로드해주세요",
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
# 데이터 전처리 함수
# -------------------
WON_FORMAT = "%,d 원"

def get_summary_item(items):
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
            
        # 헤더 자동 감지
        df_test = pd.read_excel(file_source, nrows=5)
        if hasattr(file_source, "seek"):
            file_source.seek(0)
            
        if "품목별 매입매출현황" in str(df_test.columns[0]) or "Unnamed:" in str(df_test.columns[1]):
            df = pd.read_excel(file_source, header=2)
        else:
            df = pd.read_excel(file_source)
        
        required_cols = ["제조사", "품목", "입고", "매입금", "매출금", "이익금"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"다음 필수 컬럼을 찾지 못했습니다 : {missing}")
            st.stop()

        # ==========================================
        # ★ 핵심 수정: 엑셀 '셀 병합' 문제 해결 로직 ★
        # ==========================================
        # 1. 원본 맨 밑에 있는 '합계' 줄 제거
        if '소분류' in df.columns:
            df = df[df['소분류'] != '합계'] 
        
        # 2. 셀 병합으로 인해 비어있는 칸(NaN)을 바로 위의 값으로 끌어내려 채우기 (Forward Fill)
        fill_cols = ['소분류', '품목', '규격', '제조사']
        for col in fill_cols:
            if col in df.columns:
                df[col] = df[col].ffill()
                
        # 3. 혹시라도 원본 자체에 진짜로 비어있는 값이 있다면 기본값으로 채우기
        df['품목'] = df['품목'].fillna('품목 미상')
        df['제조사'] = df['제조사'].fillna('미상(기타)')
        df['규격'] = df['규격'].fillna('-')

        # 숫자형 데이터 콤마 제거 및 형변환
        num_cols = ['입고', '매입단가', '매출단가', '매입금', '매출금', '이익금']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # 제조사 분리 로직 (엔터 기준 분리 후 금액/수량 동일값 복사)
        df['제조사_list'] = df['제조사'].astype(str).str.split('\n')
        df_exploded = df.explode('제조사_list')
        df_exploded['제조사(매입처)'] = df_exploded['제조사_list'].str.strip()

        # ==========================================
        # 탭(Tab) 레이아웃 생성
        # ==========================================
        tab_sales, tab_purchase = st.tabs(["💰 1. 매출(수익) 분석 대시보드", "🛒 2. 매입(지출) 분석 대시보드"])

        # ---------------------------------------------------------
        # [ 탭 1 ] 매출(수익) 분석 대시보드
        # ---------------------------------------------------------
        with tab_sales:
            sales_df = df_exploded[df_exploded['매출금'] > 0].copy()
            
            if sales_df.empty:
                st.info("이 엑셀 파일에는 '매출' 데이터가 존재하지 않거나, 아직 매출액이 발생하지 않았습니다.")
            else:
                report_summary = sales_df.groupby('제조사(매입처)', dropna=False).agg(
                    품목=('품목', get_summary_item),
                    총매입금=('매입금', 'sum'),
                    매출수량=('입고', 'sum'),
                    총매출금=('매출금', 'sum'),
                    매출총이익=('이익금', 'sum')
                ).reset_index()

                report_summary['당월 이익률(%)'] = (report_summary['매출총이익'] / report_summary['총매출금'] * 100).fillna(0)
                report_summary = report_summary[['제조사(매입처)', '품목', '매출수량', '총매입금', '총매출금', '매출총이익', '당월 이익률(%)']]
                report_summary.sort_values(by='총매출금', ascending=False, inplace=True)
                report_summary.rename(columns={'제조사(매입처)': '매입처'}, inplace=True)

                st.subheader("📑 본사 물류수익 마감보고서 전체현황")
                output_sales = io.BytesIO()
                with pd.ExcelWriter(output_sales, engine='openpyxl') as writer:
                    report_summary.to_excel(writer, index=False, sheet_name='매출수익 마감')
                output_sales.seek(0)
                st.download_button(
                    label="📥 물류수익 마감보고서 엑셀 다운로드",
                    data=output_sales,
                    file_name="물류수익_마감보고서.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="sales_download"
                )

                total_sales = report_summary["총매출금"].sum()
                total_profit = report_summary["매출총이익"].sum()
                avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

                c1, c2, c3 = st.columns(3)
                c1.metric("총 매출금", f"{total_sales:,.0f} 원")
                c2.metric("총 이익금", f"{total_profit:,.0f} 원")
                c3.metric("평균 이익률", f"{avg_margin:.1f} %")

                st.markdown("---")
                st.markdown("#### 🏆 매출 상위 제조사 TOP 10")
                top_sales_makers = report_summary.head(10)
                fig_sales = px.bar(top_sales_makers, x="매입처", y="총매출금", text_auto='.2s')
                fig_sales.update_traces(marker_color="cornflowerblue")
                st.plotly_chart(fig_sales, use_container_width=True)

                st.markdown("#### 🥇 품목별 매출 TOP 10")
                item_sales_df = sales_df.groupby(['품목', '규격'], dropna=False).agg(
                    수량=('입고', 'sum'), 매출금=('매출금', 'sum'), 이익금=('이익금', 'sum')
                ).reset_index().sort_values(by='매출금', ascending=False).head(10)
                item_sales_df.insert(0, '순위', range(1, 11))

                st.dataframe(
                    item_sales_df, use_container_width=True, hide_index=True,
                    column_config={"매출금": st.column_config.NumberColumn(format=WON_FORMAT), "이익금": st.column_config.NumberColumn(format=WON_FORMAT)}
                )

        # ---------------------------------------------------------
        # [ 탭 2 ] 매입(지출) 분석 대시보드
        # ---------------------------------------------------------
        with tab_purchase:
            purchase_df = df_exploded[df_exploded['매입금'] > 0].copy()

            if purchase_df.empty:
                st.info("이 엑셀 파일에는 '매입' 데이터가 존재하지 않습니다.")
            else:
                purchase_summary = purchase_df.groupby('제조사(매입처)', dropna=False).agg(
                    요약품목=('품목', get_summary_item),
                    총입고수량=('입고', 'sum'),
                    총매입금=('매입금', 'sum')
                ).reset_index()
                
                purchase_summary.sort_values(by='총매입금', ascending=False, inplace=True)
                purchase_summary.rename(columns={'제조사(매입처)': '매입처'}, inplace=True)

                st.subheader("📑 본사 매입현황 총괄표 (전체현황)")
                
                output_purch = io.BytesIO()
                with pd.ExcelWriter(output_purch, engine='openpyxl') as writer:
                    purchase_summary.to_excel(writer, index=False, sheet_name='매입현황 총괄')
                output_purch.seek(0)
                
                st.download_button(
                    label="📥 본사 매입현황 총괄표 엑셀 다운로드",
                    data=output_purch,
                    file_name="본사_매입현황_총괄.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="purch_download"
                )

                st.dataframe(
                    purchase_summary,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "총입고수량": st.column_config.NumberColumn(format="%d"),
                        "총매입금": st.column_config.NumberColumn(format=WON_FORMAT)
                    }
                )

                st.markdown("---")
                total_purchase = purchase_summary["총매입금"].sum()
                total_qty = purchase_summary["총입고수량"].sum()
                avg_unit_price = (total_purchase / total_qty) if total_qty > 0 else 0

                c1, c2, c3 = st.columns(3)
                c1.metric("총 매입금 (지출 총액)", f"{total_purchase:,.0f} 원")
                c2.metric("총 매입(입고) 수량", f"{total_qty:,.0f} 단위")
                c3.metric("평균 매입단가 (전체 평균)", f"{avg_unit_price:,.0f} 원")

                st.markdown("---")
                st.markdown("#### 🏢 매입 비중이 가장 높은 제조사 TOP 10")
                top_purchase_makers = purchase_summary.head(10)
                
                fig_purchase = px.bar(top_purchase_makers, x="매입처", y="총매입금", text_auto='.2s')
                fig_purchase.update_traces(marker_color="#FF6B6B") 
                fig_purchase.update_layout(yaxis_tickformat=",.0f")
                st.plotly_chart(fig_purchase, use_container_width=True)

                st.markdown("#### 🥇 매입(지출)이 가장 많은 품목 TOP 10")
                item_purchase_df = purchase_df.groupby(['품목', '규격'], dropna=False).agg(
                    입고수량=('입고', 'sum'), 
                    평균매입단가=('매입단가', 'mean'), 
                    매입금액=('매입금', 'sum')
                ).reset_index().sort_values(by='매입금액', ascending=False).head(10)
                
                item_purchase_df.insert(0, '순위', range(1, 11))

                st.dataframe(
                    item_purchase_df, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "순위": st.column_config.NumberColumn(format="%d위"),
                        "입고수량": st.column_config.NumberColumn(format="%d"),
                        "평균매입단가": st.column_config.NumberColumn(format=WON_FORMAT), 
                        "매입금액": st.column_config.NumberColumn(format=WON_FORMAT)
                    }
                )

    except Exception as e:
        st.error(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")
