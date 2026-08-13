import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="꾸브라꼬 메뉴별 매출 대시보드", layout="wide")
st.title("🍗 꾸브라꼬 메뉴별 매출 분석 대시보드")
st.markdown("수많은 메뉴들을 **치킨, 세트, 사이드, 추가건들** 및 **뼈/순살**로 자동 분류하여 분석합니다.")

# -------------------
# 분류 자동화 함수
# -------------------
def get_menu_category(menu):
    menu = str(menu).strip()
    # 1. 옵션/추가건/포장/배달 등
    if menu.startswith('-') or menu.startswith('+') or '배달' in menu or '포장' in menu or '홀매출' in menu or '추가' in menu:
        return '추가건들(옵션/기타)'
        
    # 2. 세트 메뉴
    if '세트' in menu or '&' in menu or '+' in menu:
        return '세트'
        
    # 3. 사이드 메뉴 (치킨무, 사리, 음료 등)
    if any(k in menu for k in ['사리', '똥집', '치즈볼', '음료', '콜라', '사이다', '튀김', '밥', '햇반', '감자', '떡', '소스', '무', '우동']):
        return '사이드'
        
    # 4. 치킨 단품
    if any(k in menu for k in ['꾸브', '후라이드', '치킨', '반반']):
        return '치킨'
        
    # 위 조건에 안 맞으면 기타로 분류
    return '추가건들(옵션/기타)'

def get_bone_type(menu):
    menu = str(menu).strip()
    cat = get_menu_category(menu)
    
    # 사이드나 추가건들은 뼈/순살을 구분하지 않음
    if cat in ['사이드', '추가건들(옵션/기타)']:
        return '-'
        
    # 치킨, 세트 중에서 '순살' 단어가 있으면 순살, 없으면 기본 뼈
    if '순살' in menu:
        return '순살'
    else:
        return '뼈'

# -------------------
# 파일 업로드 및 분석 로직
# -------------------
uploaded_file = st.file_uploader("메뉴별 매출분석 엑셀 파일을 업로드해주세요", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 메뉴별 매출 분석 파일은 2번째 줄(header=1)부터 컬럼명이 시작됨
        df = pd.read_excel(uploaded_file, header=1)
        
        # 합계 행 및 메뉴명이 없는 불필요한 데이터 제거
        data = df.dropna(subset=['메뉴명']).copy()
        data = data[data['메뉴명'] != '합계']
        
        # 필수 데이터인 메뉴명, 판매수량, 실매출액만 추출
        req_cols = ['메뉴명', '판매수량', '실매출액']
        missing = [c for c in req_cols if c not in data.columns]
        if missing:
            st.error(f"엑셀 파일에서 다음 컬럼을 찾지 못했습니다: {missing}")
            st.stop()
            
        data = data[['메뉴명', '판매수량', '실매출액']]
        data['판매수량'] = pd.to_numeric(data['판매수량'], errors='coerce').fillna(0)
        data['실매출액'] = pd.to_numeric(data['실매출액'], errors='coerce').fillna(0)
        
        # 앞서 만든 자동 분류 규칙 적용하기
        data['메뉴분류'] = data['메뉴명'].apply(get_menu_category)
        data['뼈/순살'] = data['메뉴명'].apply(get_bone_type)
        
        # -------------------
        # 전체 요약 지표
        # -------------------
        total_sales = data['실매출액'].sum()
        total_qty = data['판매수량'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("전체 실매출액", f"{total_sales:,.0f} 원")
        col2.metric("전체 판매수량", f"{total_qty:,.0f} 개")
        st.markdown("---")
        
        # -------------------
        # 1. 메뉴 분류별 매출 (원형 차트)
        # -------------------
        st.header("📊 1. 카테고리별 매출 분석 (치킨/세트/사이드 등)")
        cat_sales = data.groupby('메뉴분류')[['실매출액', '판매수량']].sum().reset_index()
        cat_sales = cat_sales.sort_values('실매출액', ascending=False)
        
        fig_cat = px.pie(cat_sales, names='메뉴분류', values='실매출액', hole=0.4)
        fig_cat.update_traces(textposition="inside", textinfo="percent+label")
        
        col_chart1, col_table1 = st.columns([1, 1])
        with col_chart1:
            st.plotly_chart(fig_cat, use_container_width=True)
        with col_table1:
            st.dataframe(cat_sales, use_container_width=True, hide_index=True,
                         column_config={"실매출액": st.column_config.NumberColumn(format="%,d 원"),
                                        "판매수량": st.column_config.NumberColumn(format="%,d 개")})
                                        
        st.markdown("---")
        
        # -------------------
        # 2. 뼈 vs 순살 매출 비교
        # -------------------
        st.header("🦴 2. 뼈 vs 순살 매출 비교 (치킨 & 세트 한정)")
        bone_data = data[data['뼈/순살'] != '-']
        bone_sales = bone_data.groupby('뼈/순살')[['실매출액', '판매수량']].sum().reset_index()
        
        fig_bone = px.pie(bone_sales, names='뼈/순살', values='실매출액', color='뼈/순살', hole=0.4,
                          color_discrete_map={"뼈": "#8c564b", "순살": "#ff7f0e"})
        fig_bone.update_traces(textposition="inside", textinfo="percent+label")
        
        col_chart2, col_table2 = st.columns([1, 1])
        with col_chart2:
            st.plotly_chart(fig_bone, use_container_width=True)
        with col_table2:
            st.dataframe(bone_sales, use_container_width=True, hide_index=True,
                         column_config={"실매출액": st.column_config.NumberColumn(format="%,d 원"),
                                        "판매수량": st.column_config.NumberColumn(format="%,d 개")})
                                        
        st.markdown("---")
        
        # -------------------
        # 3. 전체 메뉴 TOP 20
        # -------------------
        st.header("🏆 3. 전체 메뉴 매출 TOP 20")
        top20 = data.sort_values('실매출액', ascending=False).head(20)
        fig_top = px.bar(top20, x='메뉴명', y='실매출액', color='메뉴분류')
        fig_top.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_top, use_container_width=True)
        
        st.markdown("---")
        
        # -------------------
        # 4. 상세 조건 검색
        # -------------------
        st.header("🔍 4. 상세 메뉴 검색")
        
        scol1, scol2, scol3 = st.columns(3)
        with scol1:
            sel_cat = st.selectbox("메뉴 분류 필터", ["전체"] + list(data['메뉴분류'].unique()))
        with scol2:
            sel_bone = st.selectbox("뼈/순살 필터", ["전체"] + list(data['뼈/순살'].unique()))
        with scol3:
            search_kw = st.text_input("메뉴명 검색 (예: 우동사리)")
            
        filtered = data.copy()
        if sel_cat != "전체":
            filtered = filtered[filtered['메뉴분류'] == sel_cat]
        if sel_bone != "전체":
            filtered = filtered[filtered['뼈/순살'] == sel_bone]
        if search_kw:
            filtered = filtered[filtered['메뉴명'].str.contains(search_kw, na=False)]
            
        filtered = filtered.sort_values('실매출액', ascending=False)
        st.dataframe(filtered, use_container_width=True, hide_index=True,
                     column_config={"실매출액": st.column_config.NumberColumn(format="%,d 원"),
                                    "판매수량": st.column_config.NumberColumn(format="%,d 개")})
                                    
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")