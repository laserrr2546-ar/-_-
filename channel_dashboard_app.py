import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="매장별 플랫폼/채널 매출 분석", layout="wide")
st.title("🛵 매장별 주문채널(플랫폼) 매출 분석")
st.markdown("매장명을 검색하여 어느 배달 플랫폼이나 채널에서 매출이 많이 발생하는지 즉시 확인합니다.")

# -------------------
# 파일 업로드
# -------------------
uploaded_file = st.file_uploader("주문경로별 매출분석(매장별) 엑셀 파일을 업로드해주세요", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 데이터 로드 (헤더는 2번째 줄)
        df = pd.read_excel(uploaded_file, header=1)
        
        # 합계 및 빈 데이터 제거
        data = df.dropna(subset=['매장명', '주문채널 상세']).copy()
        data = data[data['매장명'] != '합계']
        data = data[data['주문구분'] != '합계']
        
        # 필수 컬럼 확인
        req_cols = ['매장명', '주문채널 상세', '건수', '실 매출액']
        if not all(col in data.columns for col in req_cols):
            st.error(f"필수 컬럼이 없습니다. 엑셀 파일을 확인해주세요. (필요 컬럼: {req_cols})")
            st.stop()
            
        # 숫자형 변환 (오류 방지)
        data['건수'] = pd.to_numeric(data['건수'], errors='coerce').fillna(0)
        data['실 매출액'] = pd.to_numeric(data['실 매출액'], errors='coerce').fillna(0)
        
        # -------------------
        # 매장 검색 (Selectbox - 타이핑 자동완성 지원)
        # -------------------
        st.markdown("---")
        st.header("🔍 매장 검색")
        
        store_list = sorted(data['매장명'].unique().tolist())
        
        # st.selectbox는 타이핑을 하면 자동으로 매장을 검색해줍니다.
        selected_store = st.selectbox(
            "분석할 매장명을 검색하거나 선택하세요 (예: 꾸브라꼬)",
            ["전체 매장 요약"] + store_list
        )
        
        st.markdown("---")
        
        # 검색된 매장에 맞춰 데이터 필터링
        if selected_store == "전체 매장 요약":
            st.header("🏢 전국 매장 플랫폼 전체 요약")
            filtered_data = data
        else:
            st.header(f"🏪 [{selected_store}] 플랫폼별 매출 상세")
            filtered_data = data[data['매장명'] == selected_store]
            
        # 데이터 집계 (주문채널 상세 기준)
        channel_sales = filtered_data.groupby('주문채널 상세')[['건수', '실 매출액']].sum().reset_index()
        channel_sales = channel_sales.sort_values('실 매출액', ascending=False)
        
        total_sales = channel_sales['실 매출액'].sum()
        total_orders = channel_sales['건수'].sum()
        
        # 매출비율(%) 계산
        if total_sales > 0:
            channel_sales['매출비중(%)'] = (channel_sales['실 매출액'] / total_sales * 100).round(1)
        else:
            channel_sales['매출비중(%)'] = 0
            
        # 요약 지표 화면 출력
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("총 실 매출액", f"{total_sales:,.0f} 원")
        col_m2.metric("총 주문 건수", f"{total_orders:,.0f} 건")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 차트와 표 배치
        col_chart, col_table = st.columns([1.2, 1])
        
        with col_chart:
            if total_sales > 0:
                # 파이 차트
                fig = px.pie(channel_sales, names='주문채널 상세', values='실 매출액', hole=0.4)
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("해당 매장의 매출 데이터가 없습니다.")
                
        with col_table:
            # 상세 데이터프레임
            st.dataframe(channel_sales, use_container_width=True, hide_index=True,
                         column_config={
                             "주문채널 상세": "플랫폼(채널)명",
                             "건수": st.column_config.NumberColumn("주문 건수", format="%,d 건"),
                             "매출비중(%)": st.column_config.NumberColumn("비율", format="%.1f %%"),
                             "실 매출액": st.column_config.NumberColumn("실 매출액", format="%,d 원")
                         })
                         
        # 막대 그래프 추가 비교
        if total_sales > 0:
            st.markdown("---")
            fig_bar = px.bar(channel_sales, x='주문채널 상세', y='실 매출액', color='주문채널 상세', 
                             title="채널별 매출액 비교 (막대그래프)")
            fig_bar.update_yaxes(tickformat=",.0f")
            st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")