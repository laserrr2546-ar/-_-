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
# 데이터 전처리 및 공통 함수
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

# ★ 엑셀의 '소계(부분합)' 형태를 똑같이 만들어주는 특수 함수 ★
def create_subtotal_table(df, is_sales=True):
    qty_col = '입고'
    price_col = '매출단가' if is_sales else '매입단가'
    total_col = '매출금' if is_sales else '매입금'
    
    agg_dict = {
        qty_col: 'sum',
        price_col: 'mean', # 단가는 평균으로 표기
        total_col: 'sum'
    }
    if is_sales:
        agg_dict['이익금'] = 'sum'
        
    # 1차 그룹화
    grouped = df.groupby(['제조사(매입처)', '품목', '규격'], dropna=False).agg(agg_dict).reset_index()
    # 정렬: 매입처 가나다순 -> 금액 큰 순
    grouped.sort_values(by=['제조사(매입처)', total_col], ascending=[True, False], inplace=True)
    
    final_data = []
    
    # 매입처별로 순회하며 소계 행 삽입
    for maker, group in grouped.groupby('제조사(매입처)', sort=False):
        for _, row in group.iterrows():
            final_data.append(row.to_dict())
        
        # '소계' 행 생성
        subtotal = {
            '제조사(매입처)': maker,
            '품목': f"▶ {maker} 소계",
            '규격': "",
            qty_col: group[qty_col].sum(),
            price_col: None, # 소계 줄에서는 단가를 비워둠
            total_col: group[total_col].sum()
        }
        if is_sales:
            subtotal['이익금'] = group['이익금'].sum()
        
        final_data.append(subtotal)
        
    res_df = pd.DataFrame(final_data)
    
    # 출력용 컬럼명 변경
    rename_dict = {
        '제조사(매입처)': '매입처',
        qty_col: '수량',
        price_col: '단가',
        total_col: '총금액'
    }
    res_df.rename(columns=rename_dict, inplace=True)
    return res_df


if file_source is not None:
    try:
        if hasattr(file_source, "seek"):
            file_source.seek(0)
            
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

        # 셀 병합 및 빈칸 전처리 로직
        if '소분류' in df.columns:
            df = df[df['소분류'] != '합계'] 
        
        fill_cols = ['소분류', '품목', '규격', '제조사']
        for col in fill_cols:
            if col in df.columns:
                df[col] = df[col].ffill()
                
        df['품목'] = df['품목'].fillna('품목 미상')
        df['제조사'] = df['제조사'].fillna('미상(기타)')
        df['규격'] = df['규격'].fillna('-')

        num_cols = ['입고', '매입단가', '매출단가', '매입금', '매출금', '이익금']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

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
                # 상단 요약 (생략 방지)
                report_summary = sales_df.groupby('제조사(매입처)', dropna=False).agg(
                    품목=('품목', get_summary_item), 총매입금=('매입금', 'sum'), 매출수량=('입고', 'sum'),
                    총매출금=('매출금', 'sum'), 매출총이익=('이익금', 'sum')
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
                st.download_button("📥 물류수익 마감보고서 엑셀 다운로드", data=output_sales, file_name="물류수익_마감보고서.xlsx", key="s_down")

                # KPI
                c1, c2, c3 = st.columns(3)
                c1.metric("총 매출금", f"{report_summary['총매출금'].sum():,.0f} 원")
                c2.metric("총 이익금", f"{report_summary['매출총이익'].sum():,.0f} 원")
                c3.metric("평균 이익률", f"{(report_summary['매출총이익'].sum() / report_summary['총매출금'].sum() * 100) if report_summary['총매출금'].sum()>0 else 0:.1f} %")

                st.markdown("---")
                
                # 차트
                fig_sales = px.bar(report_summary.head(10), x="매입처", y="총매출금", title="🏆 매출 상위 제조사 TOP 10", text_auto='.2s')
                fig_sales.update_traces(marker_color="cornflowerblue")
                st.plotly_chart(fig_sales, use_container_width=True)

                # ==========================================
                # [매출] 상세품목 및 소계 테이블
                # ==========================================
                st.markdown("#### 🔍 매입처별 - 품목별 상세 매출내역 (소계 포함)")
                st.caption("※ 각 매입처 하단에 '▶ OOO 소계' 행이 자동으로 추가되어 전체 합산을 보여줍니다.")
                
                sales_detail_df = create_subtotal_table(sales_df, is_sales=True)

                # 스타일링: '소계'라는 글자가 들어간 행의 배경색을 노란색으로 강조
                def highlight_subtotal(row):
                    if "소계" in str(row['품목']):
                        return ['background-color: #fff3b0; font-weight: bold; color: black;'] * len(row)
                    return [''] * len(row)
                
                st.dataframe(
                    sales_detail_df.style.apply(highlight_subtotal, axis=1).format({
                        "수량": "{:,.0f}", "단가": "{:,.0f}", "총금액": "{:,.0f}", "이익금": "{:,.0f}"
                    }, na_rep=""),
                    use_container_width=True,
                    height=600,
                    hide_index=True
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
                    요약품목=('품목', get_summary_item), 총입고수량=('입고', 'sum'), 총매입금=('매입금', 'sum')
                ).reset_index()
                purchase_summary.sort_values(by='총매입금', ascending=False, inplace=True)
                purchase_summary.rename(columns={'제조사(매입처)': '매입처'}, inplace=True)

                st.subheader("📑 본사 매입현황 총괄표 (전체현황)")
                output_purch = io.BytesIO()
                with pd.ExcelWriter(output_purch, engine='openpyxl') as writer:
                    purchase_summary.to_excel(writer, index=False, sheet_name='매입현황 총괄')
                output_purch.seek(0)
                st.download_button("📥 본사 매입현황 총괄표 엑셀 다운로드", data=output_purch, file_name="본사_매입현황_총괄.xlsx", key="p_down")

                # KPI
                c1, c2, c3 = st.columns(3)
                c1.metric("총 매입금 (지출 총액)", f"{purchase_summary['총매입금'].sum():,.0f} 원")
                c2.metric("총 매입(입고) 수량", f"{purchase_summary['총입고수량'].sum():,.0f} 단위")
                c3.metric("평균 매입단가", f"{(purchase_summary['총매입금'].sum() / purchase_summary['총입고수량'].sum()) if purchase_summary['총입고수량'].sum()>0 else 0:.0f} 원")

                st.markdown("---")
                
                # 차트
                fig_purchase = px.bar(purchase_summary.head(10), x="매입처", y="총매입금", title="🏢 매입 비중 최고 제조사 TOP 10", text_auto='.2s')
                fig_purchase.update_traces(marker_color="#FF6B6B") 
                st.plotly_chart(fig_purchase, use_container_width=True)

                # ==========================================
                # [매입] 상세품목 및 소계 테이블
                # ==========================================
                st.markdown("#### 🔍 매입처별 - 품목별 상세 매입내역 (소계 포함)")
                st.caption("※ 각 매입처 하단에 '▶ OOO 소계' 행이 자동으로 추가되어 전체 합산을 보여줍니다.")

                purchase_detail_df = create_subtotal_table(purchase_df, is_sales=False)

                # 매입탭 소계는 연한 붉은색(핑크)으로 강조
                def highlight_purch_subtotal(row):
                    if "소계" in str(row['품목']):
                        return ['background-color: #ffd6d6; font-weight: bold; color: black;'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    purchase_detail_df.style.apply(highlight_purch_subtotal, axis=1).format({
                        "수량": "{:,.0f}", "단가": "{:,.0f}", "총금액": "{:,.0f}"
                    }, na_rep=""),
                    use_container_width=True,
                    height=600,
                    hide_index=True
                )

    except Exception as e:
        st.error(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")
