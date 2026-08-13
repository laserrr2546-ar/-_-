import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="꾸브라꼬 상세 메뉴 분석", layout="wide")
st.title("🍗 꾸브라꼬 핵심 지표 및 판매비율 분석")
st.markdown("주력 메뉴의 판매 비중, 세트 vs 단품, 사이드 메뉴, 뼈 vs 순살 선호도를 심층 분석합니다.")

# -------------------
# 분류 자동화 함수
# -------------------
def get_target_chicken(menu):
    # 띄어쓰기나 기호(℃) 등에 구애받지 않도록 텍스트 전처리
    m = str(menu).replace(' ', '').replace('℃', '도')
    
    # 우선순위 주의: '저당양념'이 '양념'보다 먼저 와야 정확히 분류됨
    if '저당양념' in m: return '저당양념꾸브'
    elif '양념꾸브' in m: return '양념꾸브'
    elif '트러플' in m: return '트러플꾸브'
    elif '소금' in m: return '소금꾸브'
    elif '로제' in m: return '로제꾸브'
    elif '까르보' in m: return '까르보꾸브'
    elif '데리' in m: return '데리꾸브'
    elif '170도후라이드' in m: return '170도후라이드'
    elif '170도양념' in m: return '170도양념치킨'
    elif '170도간장' in m: return '170도간장치킨'
    
    return '기타메뉴'

def get_menu_type(menu):
    m = str(menu).strip()
    # 배달비, 포장할인, 옵션 추가 등의 허수 데이터 제외
    if m.startswith('-') or m.startswith('+') or '배달' in m or '포장' in m or '추가' in m or '홀매출' in m:
        return '제외(옵션/기타)'
        
    if '세트' in m or '&' in m:
        return '세트'
    elif any(k in m for k in ['사리', '똥집', '치즈볼', '음료', '콜라', '사이다', '튀김', '밥', '햇반', '감자', '떡', '소스', '무', '우동']):
        return '사이드'
    elif any(k in m for k in ['꾸브', '후라이드', '치킨', '반반']):
        return '단품'
        
    return '제외(옵션/기타)'

def get_bone_type(menu, menu_type):
    # 뼈/순살은 치킨(단품)과 세트 메뉴에서만 구분
    if menu_type in ['세트', '단품']:
        if '순살' in str(menu):
            return '순살'
        else:
            return '뼈'
    return '-'

# -------------------
# 파일 업로드 및 분석
# -------------------
uploaded_file = st.file_uploader("메뉴별 매출분석 엑셀 파일을 업로드해주세요", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 데이터 불러오기 (헤더는 2번째 줄)
        df = pd.read_excel(uploaded_file, header=1)
        
        data = df.dropna(subset=['메뉴명']).copy()
        data = data[data['메뉴명'] != '합계']
        
        req_cols = ['메뉴명', '판매수량', '실매출액']
        if not all(col in data.columns for col in req_cols):
            st.error("필수 컬럼(메뉴명, 판매수량, 실매출액)이 없습니다. 파일을 확인해주세요.")
            st.stop()
            
        data = data[['메뉴명', '판매수량', '실매출액']]
        data['판매수량'] = pd.to_numeric(data['판매수량'], errors='coerce').fillna(0)
        data['실매출액'] = pd.to_numeric(data['실매출액'], errors='coerce').fillna(0)
        
        # 분석용 컬럼 생성 적용
        data['주력메뉴분류'] = data['메뉴명'].apply(get_target_chicken)
        data['메뉴형태'] = data['메뉴명'].apply(get_menu_type)
        data['뼈_순살'] = data.apply(lambda x: get_bone_type(x['메뉴명'], x['메뉴형태']), axis=1)

        # '판매비율'을 직관적으로 보기 위해 파이 차트는 '판매수량'을 기준으로 그립니다.
        
        # ==========================================
        # 1. 특정 주력 메뉴 판매 비율
        # ==========================================
        st.markdown("---")
        st.header("🏆 1. 핵심 주력 메뉴 판매 비율")
        st.caption("요청하신 10가지 특정 메뉴들 간의 판매수량 비중입니다. (세트/단품 모두 포함)")
        
        target_data = data[data['주력메뉴분류'] != '기타메뉴']
        target_sales = target_data.groupby('주력메뉴분류')[['판매수량', '실매출액']].sum().reset_index()
        target_sales = target_sales.sort_values('판매수량', ascending=False)
        
        col1, col2 = st.columns([1.2, 1])
        with col1:
            fig1 = px.pie(target_sales, names='주력메뉴분류', values='판매수량', hole=0.3)
            fig1.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            st.dataframe(target_sales, use_container_width=True, hide_index=True,
                         column_config={"판매수량": st.column_config.NumberColumn("판매 건수", format="%,d 개"),
                                        "실매출액": st.column_config.NumberColumn("실매출액", format="%,d 원")})

        # ==========================================
        # 2. 세트 vs 단품 판매 비율
        # ==========================================
        st.markdown("---")
        st.header("🍔 2. 세트 vs 단품 판매 비율")
        
        type_data = data[data['메뉴형태'].isin(['세트', '단품'])]
        type_sales = type_data.groupby('메뉴형태')[['판매수량', '실매출액']].sum().reset_index()
        
        col3, col4 = st.columns([1.2, 1])
        with col3:
            fig2 = px.pie(type_sales, names='메뉴형태', values='판매수량', hole=0.3,
                          color_discrete_sequence=['#4C78A8', '#F58518'])
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig2, use_container_width=True)
        with col4:
            st.dataframe(type_sales, use_container_width=True, hide_index=True,
                         column_config={"판매수량": st.column_config.NumberColumn("판매 건수", format="%,d 개"),
                                        "실매출액": st.column_config.NumberColumn("실매출액", format="%,d 원")})

        # ==========================================
        # 3. 사이드 제품 판매 비율
        # ==========================================
        st.markdown("---")
        st.header("🍟 3. 사이드 메뉴 판매 비율")
        
        side_data = data[data['메뉴형태'] == '사이드']
        side_sales = side_data.groupby('메뉴명')[['판매수량', '실매출액']].sum().reset_index()
        side_sales = side_sales.sort_values('판매수량', ascending=False)
        
        # 사이드 메뉴가 너무 많을 수 있으므로 차트는 상위 15개만 표시
        top_sides = side_sales.head(15)
        
        col5, col6 = st.columns([1.2, 1])
        with col5:
            fig3 = px.pie(top_sides, names='메뉴명', values='판매수량', hole=0.3)
            fig3.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig3, use_container_width=True)
            st.caption("* 차트는 판매 건수 기준 상위 15개 사이드 메뉴만 표시됩니다.")
        with col6:
            st.dataframe(side_sales, use_container_width=True, hide_index=True, height=400,
                         column_config={"판매수량": st.column_config.NumberColumn("판매 건수", format="%,d 개"),
                                        "실매출액": st.column_config.NumberColumn("실매출액", format="%,d 원")})

        # ==========================================
        # 4. 뼈 vs 순살 판매 비율
        # ==========================================
        st.markdown("---")
        st.header("🦴 4. 뼈 vs 순살 선호도 (세트/단품 한정)")
        
        bone_data = data[data['뼈_순살'] != '-']
        bone_sales = bone_data.groupby('뼈_순살')[['판매수량', '실매출액']].sum().reset_index()
        
        col7, col8 = st.columns([1.2, 1])
        with col7:
            fig4 = px.pie(bone_sales, names='뼈_순살', values='판매수량', hole=0.3,
                          color_discrete_map={"뼈": "#8c564b", "순살": "#ff7f0e"})
            fig4.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig4, use_container_width=True)
        with col8:
            st.dataframe(bone_sales, use_container_width=True, hide_index=True,
                         column_config={"판매수량": st.column_config.NumberColumn("판매 건수", format="%,d 개"),
                                        "실매출액": st.column_config.NumberColumn("실매출액", format="%,d 원")})

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
