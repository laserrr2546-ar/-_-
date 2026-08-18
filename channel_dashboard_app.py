import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="매장별 플랫폼/채널 매출 분석", layout="wide")
st.title("🛵 매장별 주문경로 및 플랫폼 심층 분석")
st.markdown("전국 매장의 지역/권역별 리스트를 확인하고, **온라인/오프라인 비중, 플랫폼 점유율, 포장 매출 비율**을 한눈에 분석합니다.")

# -------------------
# 권역 및 지역 분류 함수
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
        
        # 포장 컬럼 이름 변경
        df = df.rename(columns={'건수.3': '포장건수', '실 매출액.3': '포장매출액'})
        
        # 결측치 및 합계 행 제거 (주문채널 대분류, 소분류 모두 체크)
        data = df.dropna(subset=['매장명', '주문채널', '주문채널 상세']).copy()
        data = data[data['매장명'] != '합계']
        data = data[data['주문구분'] != '합계']
        
        # 숫자형 변환
        for col in ['실 매출액', '포장매출액', '건수', '포장건수']:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            
        data['지역'] = data['매장명'].apply(get_region)
        data['권역'] = data['지역'].apply(get_area)

        # ==========================================
        # 1. 상단: 전체 요약 및 개별 매장 상세 검색
        # ==========================================
        st.markdown("---")
        st.header("🔍 매장 종합/개별 집중 분석")
        
        store_list = sorted(data['매장명'].unique().tolist())
        selected_store = st.selectbox(
            "타이핑하여 매장명을 검색하거나 선택하세요 (기본값: 전체 매장 요약)",
            ["전체 매장 요약"] + store_list
        )
        
        # ✨ 새로 추가된 조회 기준 선택 스위치
        st.markdown("<br>", unsafe_allow_html=True)
        view_type = st.radio(
            "📊 플랫폼 분석 기준 선택", 
            ["주문채널 (대분류 - 예: 배달의민족, 포스, 요기요 등)", "주문채널 상세 (소분류 - 예: 배민배달, MATE 태블릿 등)"], 
            horizontal=True
        )
        target_col = '주문채널 상세' if '상세' in view_type else '주문채널'

        if selected_store == "전체 매장 요약":
            st.subheader("🏢 전국 매장 플랫폼 전체 요약 데이터")
            f_data = data.copy()
        else:
            st.subheader(f"🏪 [{selected_store}] 플랫폼 상세 분석")
            f_data = data[data['매장명'] == selected_store].copy()
            
        tot_sales = f_data['실 매출액'].sum()
        on_sales = f_data[f_data['주문구분'] == '온라인']['실 매출액'].sum()
        off_sales = f_data[f_data['주문구분'] == '오프라인']['실 매출액'].sum()
        take_sales = f_data['포장매출액'].sum()
        
        on_rt = (on_sales / tot_sales * 100) if tot_sales > 0 else 0
        off_rt = (off_sales / tot_sales * 100) if tot_sales > 0 else 0
        take_rt = (take_sales / tot_sales * 100) if tot_sales > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 실매출액", f"{tot_sales:,.0f} 원")
        col2.metric("온라인 매출", f"{on_sales:,.0f} 원", f"비중 {on_rt:.1f}%", delta_color="off")
        col3.metric("오프라인 매출", f"{off_sales:,.0f} 원", f"비중 {off_rt:.1f}%", delta_color="off")
        col4.metric("포장 매출액", f"{take_sales:,.0f} 원", f"비중 {take_rt:.1f}%", delta_color="off")
        
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
            # 선택한 대/소분류 기준에 따라 차트 자동 변경
            channel_pie = f_data.groupby(target_col)['실 매출액'].sum().reset_index()
            channel_pie = channel_pie[channel_pie['실 매출액'] > 0]
            fig3 = px.pie(channel_pie, names=target_col, values='실 매출액', title="🛵 플랫폼 점유율", hole=0.3)
            fig3.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown(f"#### 📊 {target_col}별 상세 내역 표")
        
        # 선택한 대/소분류 기준에 따라 표 자동 변경
        channel_detail = f_data.groupby(target_col)[['건수', '실 매출액']].sum().reset_index()
        channel_detail = channel_detail.sort_values('실 매출액', ascending=False)
        channel_detail = channel_detail[channel_detail['실 매출액'] > 0]
        
        if tot_sales > 0:
            channel_detail['매출비중(%)'] = (channel_detail['실 매출액'] / tot_sales * 100).round(1)
        else:
            channel_detail['매출비중(%)'] = 0
            
        st.dataframe(channel_detail, use_container_width=True, hide_index=True,
                     column_config={
                         target_col: "플랫폼(채널)명",
                         "건수": st.column_config.NumberColumn("주문 건수", format="%,d 건"),
                         "매출비중(%)": st.column_config.NumberColumn("비율", format="%.1f %%"),
                         "실 매출액": st.column_config.NumberColumn("실 매출액", format="%,d 원")
                     })

        # ==========================================
        # 2. 하단: 전국 매장 종합 리스트
        # ==========================================
        st.markdown("---")
        st.header("📋 전국 매장 종합 리스트 (지역/권역 조회)")
        
        agg_tot = data.groupby(['권역', '지역', '매장명'])[['실 매출액', '포장매출액']].sum().reset_index()
        agg_tot = agg_tot.rename(columns={'실 매출액': '총매출액'})
        
        agg_on = data[data['주문구분'] == '온라인'].groupby('매장명')['실 매출액'].sum().reset_index().rename(columns={'실 매출액': '온라인매출'})
        agg_off = data[data['주문구분'] == '오프라인'].groupby('매장명')['실 매출액'].sum().reset_index().rename(columns={'실 매출액': '오프라인매출'})
        
        store_group = agg_tot.merge(agg_on, on='매장명', how='left').merge(agg_off, on='매장명', how='left')
        store_group['온라인매출'] = store_group['온라인매출'].fillna(0)
        store_group['오프라인매출'] = store_group['오프라인매출'].fillna(0)
        
        store_group['포장비율(%)'] = (store_group['포장매출액'] / store_group['총매출액'] * 100).fillna(0).round(1)
        store_group['온라인비율(%)'] = (store_group['온라인매출'] / store_group['총매출액'] * 100).fillna(0).round(1)
        
        # 선택한 기준(주문채널 or 주문채널 상세)에 맞춰서 매장별 1위 플랫폼 계산
        agg_plat = data.groupby(['매장명', target_col])['실 매출액'].sum().reset_index()
        top_plat = agg_plat.sort_values(['매장명', '실 매출액'], ascending=[True, False]).drop_duplicates('매장명')[['매장명', target_col]]
        top_plat = top_plat.rename(columns={target_col: '1위플랫폼'})
        
        store_group = store_group.merge(top_plat, on='매장명', how='left')
        
        scol1, scol2 = st.columns(2)
        with scol1:
            sel_area = st.selectbox("권역 필터", ["전체"] + sorted(store_group['권역'].unique().tolist()))
        with scol2:
            search_kw = st.text_input("매장명 검색 (예: 진해)")
            
        filtered_list = store_group.copy()
        if sel_area != "전체":
            filtered_list = filtered_list[filtered_list['권역'] == sel_area]
        if search_kw:
            filtered_list = filtered_list[filtered_list['매장명'].str.contains(search_kw, case=False, na=False)]
            
        filtered_list = filtered_list.sort_values('총매출액', ascending=False)
        
        final_cols = ['권역', '지역', '매장명', '총매출액', '온라인매출', '온라인비율(%)', '오프라인매출', '포장매출액', '포장비율(%)', '1위플랫폼']
        filtered_list = filtered_list[final_cols]
        
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
