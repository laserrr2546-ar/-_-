import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="매장별 플랫폼/채널 매출 분석", layout="wide")
st.title("🛵 매장별 주문경로 및 플랫폼 심층 분석")
st.markdown("전국 매장의 지역/권역별 리스트를 확인하고, **온라인/오프라인 비중, 플랫폼 점유율, 포장 매출 비율**을 한눈에 분석합니다.")

# -------------------
# 권역 및 지역 분류 함수 (1번째 대시보드와 동일한 로직)
# -------------------
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
    if region in ["서울", "경기", "인천", "대전", "강원", "충청(충남/충북)"]: return "수도권"
    if region in ["부산", "울산", "대구", "경상(경남/경북)"]: return "영남권"
    if region in ["광주", "전라(전남/전북)"]: return "호남권"
    if region == "제주": return "제주권"
    return "기타(미분류)"

# -------------------
# 파일 업로드 및 분석
# -------------------
uploaded_file = st.file_uploader("주문경로별 매출분석(매장별) 엑셀 파일을 업로드해주세요", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 데이터 로드 (헤더는 2번째 줄)
        df = pd.read_excel(uploaded_file, header=1)
        
        # 💡 핵심 로직: 엑셀에서 '포장'에 해당하는 컬럼(건수.3, 실 매출액.3) 이름 변경
        df = df.rename(columns={'건수.3': '포장건수', '실 매출액.3': '포장매출액'})
        
        # 결측치 및 합계 행 제거
        data = df.dropna(subset=['매장명', '주문채널 상세']).copy()
        data = data[data['매장명'] != '합계']
        data = data[data['주문구분'] != '합계']
        
        # 숫자형 변환
        for col in ['실 매출액', '포장매출액', '건수', '포장건수']:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            
        # 지역 및 권역 데이터 생성
        data['지역'] = data['매장명'].apply(get_region)
        data['권역'] = data['지역'].apply(get_area)

        # ==========================================
        # 1. 개별 매장 상세 검색 (상단부)
        # ==========================================
        st.markdown("---")
        st.header("🔍 개별 매장 집중 분석 (검색)")
        
        store_list = sorted(data['매장명'].unique().tolist())
        selected_store = st.selectbox(
            "타이핑하여 매장명을 검색하거나 선택하세요 (예: 꾸브라꼬 강릉)",
            ["전체 매장 요약"] + store_list
        )
        
        if selected_store == "전체 매장 요약":
            st.subheader("🏢 전국 매장 전체 평균 데이터")
            f_data = data.copy()
        else:
            st.subheader(f"🏪 [{selected_store}] 상세 분석")
            f_data = data[data['매장명'] == selected_store].copy()
            
        # 핵심 지표 계산
        tot_sales = f_data['실 매출액'].sum()
        on_sales = f_data[f_data['주문구분'] == '온라인']['실 매출액'].sum()
        off_sales = f_data[f_data['주문구분'] == '오프라인']['실 매출액'].sum()
        take_sales = f_data['포장매출액'].sum()
        
        on_rt = (on_sales / tot_sales * 100) if tot_sales > 0 else 0
        off_rt = (off_sales / tot_sales * 100) if tot_sales > 0 else 0
        take_rt = (take_sales / tot_sales * 100) if tot_sales > 0 else 0
        
        # 메트릭(요약 숫자) 출력
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 실매출액", f"{tot_sales:,.0f} 원")
        col2.metric("온라인 매출", f"{on_sales:,.0f} 원", f"비중 {on_rt:.1f}%", delta_color="off")
        col3.metric("오프라인 매출", f"{off_sales:,.0f} 원", f"비중 {off_rt:.1f}%", delta_color="off")
        col4.metric("포장 매출액", f"{take_sales:,.0f} 원", f"비중 {take_rt:.1f}%", delta_color="off")
        
        # 직관적인 원형 차트 3종 세트
        st.markdown("<br>", unsafe_allow_html=True)
        cc1, cc2, cc3 = st.columns(3)
        
        with cc1:
            df_onoff = pd.DataFrame({'구분': ['온라인', '오프라인'], '매출액': [on_sales, off_sales]})
            fig1 = px.pie(df_onoff, names='구분', values='매출액', title="🌐 온라인 vs 오프라인", hole=0.3,
                          color='구분', color_discrete_map={'온라인': '#636efa', '오프라인': '#ef553b'})
            fig1.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig1, use_container_width=True)
            
        with cc2:
            df_take = pd.DataFrame({'구분': ['포장 매출', '기타(배달/내점 등)'], '매출액': [take_sales, tot_sales - take_sales]})
            fig2 = px.pie(df_take, names='구분', values='매출액', title="🛍️ 전체 매출 중 포장 비율", hole=0.3,
                          color='구분', color_discrete_map={'포장 매출': '#00cc96', '기타(배달/내점 등)': '#ab63fa'})
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig2, use_container_width=True)
            
        with cc3:
            channel_sales = f_data.groupby('주문채널 상세')['실 매출액'].sum().reset_index()
            channel_sales = channel_sales[channel_sales['실 매출액'] > 0]
            fig3 = px.pie(channel_sales, names='주문채널 상세', values='실 매출액', title="🛵 플랫폼(채널)별 점유율", hole=0.3)
            fig3.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig3, use_container_width=True)

        # ==========================================
        # 2. 전국 매장 종합 리스트 (하단부)
        # ==========================================
        st.markdown("---")
        st.header("📋 전국 매장 종합 리스트 (지역/권역 조회)")
        
        # 모든 매장별 데이터 하나로 뭉치기
        agg_tot = data.groupby(['권역', '지역', '매장명'])[['실 매출액', '포장매출액']].sum().reset_index()
        agg_tot = agg_tot.rename(columns={'실 매출액': '총매출액'})
        
        agg_on = data[data['주문구분'] == '온라인'].groupby('매장명')['실 매출액'].sum().reset_index().rename(columns={'실 매출액': '온라인매출'})
        agg_off = data[data['주문구분'] == '오프라인'].groupby('매장명')['실 매출액'].sum().reset_index().rename(columns={'실 매출액': '오프라인매출'})
        
        store_group = agg_tot.merge(agg_on, on='매장명', how='left').merge(agg_off, on='매장명', how='left')
        store_group['온라인매출'] = store_group['온라인매출'].fillna(0)
        store_group['오프라인매출'] = store_group['오프라인매출'].fillna(0)
        
        # 비율 계산
        store_group['포장비율(%)'] = (store_group['포장매출액'] / store_group['총매출액'] * 100).fillna(0).round(1)
        store_group['온라인비율(%)'] = (store_group['온라인매출'] / store_group['총매출액'] * 100).fillna(0).round(1)
        
        # 매장별 1위 배달 플랫폼 찾기
        top_plat = data.sort_values(['매장명', '실 매출액'], ascending=[True, False]).drop_duplicates('매장명')[['매장명', '주문채널 상세']]
        top_plat = top_plat.rename(columns={'주문채널 상세': '1위플랫폼'})
        
        store_group = store_group.merge(top_plat, on='매장명', how='left')
        
        # 검색 UI
        scol1, scol2 = st.columns(2)
        with scol1:
            sel_area = st.selectbox("권역 필터", ["전체"] + sorted(store_group['권역'].unique().tolist()))
        with scol2:
            search_kw = st.text_input("매장명 검색 (예: 진해)")
            
        # 필터링 적용
        filtered_list = store_group.copy()
        if sel_area != "전체":
            filtered_list = filtered_list[filtered_list['권역'] == sel_area]
        if search_kw:
            filtered_list = filtered_list[filtered_list['매장명'].str.contains(search_kw, case=False, na=False)]
            
        filtered_list = filtered_list.sort_values('총매출액', ascending=False)
        
        # 보기 좋게 표 컬럼 순서 정렬
        final_cols = ['권역', '지역', '매장명', '총매출액', '온라인매출', '온라인비율(%)', '오프라인매출', '포장매출액', '포장비율(%)', '1위플랫폼']
        filtered_list = filtered_list[final_cols]
        
        # 데이터프레임(표) 출력
        st.dataframe(filtered_list, use_container_width=True, hide_index=True,
                     column_config={
                         "총매출액": st.column_config.NumberColumn(format="%,d 원"),
                         "온라인매출": st.column_config.NumberColumn(format="%,d 원"),
                         "오프라인매출": st.column_config.NumberColumn(format="%,d 원"),
                         "포장매출액": st.column_config.NumberColumn(format="%,d 원"),
                         "온라인비율(%)": st.column_config.NumberColumn(format="%.1f %%"),
                         "포장비율(%)": st.column_config.NumberColumn(format="%.1f %%"),
                     })
                     
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
