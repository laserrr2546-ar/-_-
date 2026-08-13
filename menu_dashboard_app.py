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
    m = str(menu).replace(' ', '').replace('℃', '도')
    
    if '170도후라이드' in m: return '170도후라이드'
    elif '170도양념' in m: return '170도양념치킨'
    elif '170도마늘간장' in m: return '170도마늘간장치킨'
    elif '170도간장' in m: return '170도간장치킨'
    
    if '저당양념' in m: return '저당양념꾸브'
    elif '양념꾸브' in m: return '양념꾸브'
    elif '트러플' in m: return '트러플꾸브'
    elif '소금꾸브' in m: return '소금꾸브'
    elif '로제' in m: return '로제꾸브'
    elif '까르보' in m: return '까르보꾸브'
    elif '데리꾸브' in m: return '데리꾸브'
    
    return '기타메뉴'

def get_menu_type(raw_menu):
    m = str(raw_menu)
    m_no_space = m.replace(' ', '')
    
    # 1. 예외처리: 순살 변경 '안함'은 뼈에 그대로 남아야 하므로 허수(기타) 취급
    if '안함' in m_no_space:
        return '제외(기타)'
        
    # 2. 명확한 순살 변경 옵션들 (단품 / 세트)
    if m.startswith('-') or m.startswith('+') or '순살추가' in m_no_space or '순살변경' in m_no_space:
        if '순살' in m_no_space:
            if '메뉴1' in m_no_space or '메뉴2' in m_no_space:
                return '세트순살옵션'
            else:
                return '단품순살옵션'
        else:
            return '제외(기타)'
            
    # 나머지 허수 데이터 제외
    if '배달' in m or '포장' in m_no_space or '홀매출' in m_no_space:
        return '제외(기타)'
        
    # 3. 본 품목 분류 (세트 vs 단품 vs 사이드)
    if '두마리' in m_no_space and '세트' in m_no_space:
        return '세트'
        
    if any(k in m for k in ['사리', '똥집', '치즈볼', '음료', '콜라', '사이다', '튀김', '밥', '햇반', '감자', '떡', '소스', '무', '우동']):
        return '사이드'
        
    return '단품'

def get_bone_type(raw_menu, menu_type):
    m_no_space = str(raw_menu).replace(' ', '')
    if menu_type in ['세트', '단품']:
        if '안함' in m_no_space:
            return '뼈'
        elif '순살' in m_no_space:
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
        df = pd.read_excel(uploaded_file, header=1)
        data = df.dropna(subset=['메뉴명']).copy()
        data = data[data['메뉴명'] != '합계']
        
        data['판매수량'] = pd.to_numeric(data['판매수량'], errors='coerce').fillna(0)
        data['실매출액'] = pd.to_numeric(data['실매출액'], errors='coerce').fillna(0)
        
        # 형태 분류 생성
        data['주력메뉴분류'] = data['메뉴명'].apply(get_target_chicken)
        data['메뉴형태'] = data['메뉴명'].apply(get_menu_type)
        data['뼈_순살'] = data.apply(lambda x: get_bone_type(x['메뉴명'], x['메뉴형태']), axis=1)

        # ==========================================
        # 1. 핵심 주력 메뉴 판매 비율
        # ==========================================
        st.markdown("---")
        st.header("🏆 1. 핵심 주력 메뉴 판매 비율")
        
        target_data = data[data['주력메뉴분류'] != '기타메뉴']
        target_sales = target_data.groupby('주력메뉴분류')[['판매수량', '실매출액']].sum().reset_index()
        target_sales = target_sales.sort_values('판매수량', ascending=False)
        
        target_sales['판매비율(%)'] = (target_sales['판매수량'] / target_sales['판매수량'].sum() * 100).round(1)
        
        col1, col2 = st.columns([1.2, 1])
        with col1:
            fig1 = px.pie(target_sales, names='주력메뉴분류', values='판매수량', hole=0.3)
            fig1.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            st.dataframe(target_sales, use_container_width=True, hide_index=True,
                         column_config={
                             "주력메뉴분류": "메뉴명",
                             "판매수량": st.column_config.NumberColumn("판매 건수", format="%,d 개"),
                             "판매비율(%)": st.column_config.NumberColumn("비율", format="%.1f %%"),
                             "실매출액": st.column_config.NumberColumn("실매출액", format="%,d 원")
                         })

        # ==========================================
        # 2. 세트(두마리) vs 단품 판매 비율
        # ==========================================
        st.markdown("---")
        st.header("🍔 2. 세트(두마리) vs 단품 판매 비율 (주문 건수 기준)")
        st.caption("* 두마리 세트만 '세트'로 분류되며, 별도로 결제된 순살 변경 옵션의 매출액을 세트/단품에 맞춰 합산했습니다.")
        
        type_data = data[data['메뉴형태'].isin(['세트', '단품'])]
        type_sales = type_data.groupby('메뉴형태')[['판매수량', '실매출액']].sum().reset_index()
        
        # 순살 옵션으로 발생한 매출액을 세트/단품 실매출액에 얹어주어 금액 완벽 매칭
        single_opt_rev = data.loc[data['메뉴형태'] == '단품순살옵션', '실매출액'].sum()
        set_opt_rev = data.loc[data['메뉴형태'] == '세트순살옵션', '실매출액'].sum()
        
        type_sales.loc[type_sales['메뉴형태'] == '단품', '실매출액'] += single_opt_rev
        type_sales.loc[type_sales['메뉴형태'] == '세트', '실매출액'] += set_opt_rev
        
        type_sales['판매비율(%)'] = (type_sales['판매수량'] / type_sales['판매수량'].sum() * 100).round(1)
        
        col3, col4 = st.columns([1.2, 1])
        with col3:
            fig2 = px.pie(type_sales, names='메뉴형태', values='판매수량', hole=0.3,
                          color_discrete_sequence=['#4C78A8', '#F58518'])
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig2, use_container_width=True)
        with col4:
            st.dataframe(type_sales, use_container_width=True, hide_index=True,
                         column_config={
                             "메뉴형태": "구분",
                             "판매수량": st.column_config.NumberColumn("주문 건수", format="%,d 건"),
                             "판매비율(%)": st.column_config.NumberColumn("비율", format="%.1f %%"),
                             "실매출액": st.column_config.NumberColumn("옵션합산 실매출액", format="%,d 원")
                         })

        # ==========================================
        # 3. 사이드 제품 판매 비율
        # ==========================================
        st.markdown("---")
        st.header("🍟 3. 사이드 메뉴 판매 비율")
        
        side_data = data[data['메뉴형태'] == '사이드']
        side_sales = side_data.groupby('메뉴명')[['판매수량', '실매출액']].sum().reset_index()
        side_sales = side_sales.sort_values('판매수량', ascending=False)
        
        side_sales['판매비율(%)'] = (side_sales['판매수량'] / side_sales['판매수량'].sum() * 100).round(1)
        top_sides = side_sales.head(15)
        
        col5, col6 = st.columns([1.2, 1])
        with col5:
            fig3 = px.pie(top_sides, names='메뉴명', values='판매수량', hole=0.3)
            fig3.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig3, use_container_width=True)
            st.caption("* 차트는 판매 건수 기준 상위 15개 사이드 메뉴만 표시됩니다.")
        with col6:
            st.dataframe(side_sales, use_container_width=True, hide_index=True, height=400,
                         column_config={
                             "판매수량": st.column_config.NumberColumn("판매 건수", format="%,d 개"),
                             "판매비율(%)": st.column_config.NumberColumn("비율", format="%.1f %%"),
                             "실매출액": st.column_config.NumberColumn("실매출액", format="%,d 원")
                         })

        # ==========================================
        # 4. 뼈 vs 순살 선호도 (마리 수 기준 완벽 역산)
        # ==========================================
        st.markdown("---")
        st.header("🦴 4. 뼈 vs 순살 선호도 (치킨 '마리(Piece)' 기준)")
        st.caption("※ 옵션으로 추가된 순살 변경 수량을 정확히 역산하기 위해 단품은 1마리, 세트는 2마리로 쪼개어 계산한 실제 순살 치킨 비율입니다.")
        
        # 옵션 수량 및 매출 확보
        single_opt_qty = data.loc[data['메뉴형태'] == '단품순살옵션', '판매수량'].sum()
        set_opt_qty = data.loc[data['메뉴형태'] == '세트순살옵션', '판매수량'].sum()
        
        bone_base = data[data['뼈_순살'] != '-'].groupby(['메뉴형태', '뼈_순살'])[['판매수량', '실매출액']].sum().reset_index()
        
        # 기본 뼈/순살 집계 추출
        s_bone_qty = bone_base.loc[(bone_base['메뉴형태']=='단품') & (bone_base['뼈_순살']=='뼈'), '판매수량'].sum()
        s_bone_rev = bone_base.loc[(bone_base['메뉴형태']=='단품') & (bone_base['뼈_순살']=='뼈'), '실매출액'].sum()
        s_boneless_qty = bone_base.loc[(bone_base['메뉴형태']=='단품') & (bone_base['뼈_순살']=='순살'), '판매수량'].sum()
        s_boneless_rev = bone_base.loc[(bone_base['메뉴형태']=='단품') & (bone_base['뼈_순살']=='순살'), '실매출액'].sum()
        
        set_bone_qty = bone_base.loc[(bone_base['메뉴형태']=='세트') & (bone_base['뼈_순살']=='뼈'), '판매수량'].sum()
        set_bone_rev = bone_base.loc[(bone_base['메뉴형태']=='세트') & (bone_base['뼈_순살']=='뼈'), '실매출액'].sum()
        set_boneless_qty = bone_base.loc[(bone_base['메뉴형태']=='세트') & (bone_base['뼈_순살']=='순살'), '판매수량'].sum()
        set_boneless_rev = bone_base.loc[(bone_base['메뉴형태']=='세트') & (bone_base['뼈_순살']=='순살'), '실매출액'].sum()
        
        # 뼈 치킨의 평균가 계산 (이동시킬 매출액 산출용)
        s_bone_avg = s_bone_rev / s_bone_qty if s_bone_qty > 0 else 0
        set_bone_avg_per_piece = (set_bone_rev / set_bone_qty) / 2 if set_bone_qty > 0 else 0
        
        # 역산 로직 적용 (옵션 변경분만큼 뼈에서 빼고 순살로 더해줌)
        final_bone_qty = (s_bone_qty - single_opt_qty) + (set_bone_qty * 2 - set_opt_qty)
        final_bone_rev = (s_bone_rev - single_opt_qty * s_bone_avg) + (set_bone_rev - set_opt_qty * set_bone_avg_per_piece)
        
        final_boneless_qty = (s_boneless_qty + single_opt_qty) + (set_boneless_qty * 2 + set_opt_qty)
        final_boneless_rev = (s_boneless_rev + single_opt_rev + single_opt_qty * s_bone_avg) + (set_boneless_rev + set_opt_rev + set_opt_qty * set_bone_avg_per_piece)

        # 결과 생성
        final_bone_df = pd.DataFrame({
            '구분': ['뼈', '순살'],
            '판매수량(마리)': [final_bone_qty, final_boneless_qty],
            '실매출액': [final_bone_rev, final_boneless_rev]
        })
        final_bone_df['판매비율(%)'] = (final_bone_df['판매수량(마리)'] / final_bone_df['판매수량(마리)'].sum() * 100).round(1)
        
        col7, col8 = st.columns([1.2, 1])
        with col7:
            fig4 = px.pie(final_bone_df, names='구분', values='판매수량(마리)', hole=0.3,
                          color_discrete_map={"뼈": "#8c564b", "순살": "#ff7f0e"})
            fig4.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig4, use_container_width=True)
        with col8:
            st.dataframe(final_bone_df, use_container_width=True, hide_index=True,
                         column_config={
                             "판매수량(마리)": st.column_config.NumberColumn("치킨 마리 수", format="%,d 마리"),
                             "판매비율(%)": st.column_config.NumberColumn("비율", format="%.1f %%"),
                             "실매출액": st.column_config.NumberColumn("역산 후 매출액", format="%,d 원")
                         })

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
