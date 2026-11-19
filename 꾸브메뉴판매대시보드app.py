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

def get_menu_type(raw_menu, sale_price):
    m = str(raw_menu)
    m_no_space = m.replace(' ', '')
    
    # 1. 판매가가 0원이거나 없는 경우 집계 제외(허수)
    if pd.isna(sale_price) or sale_price == 0:
        return '제외(기타)'

    # 2. 순살 변경 옵션들 처리 (주문 건수 중복 집계 방지)
    if '안함' in m_no_space:
        return '제외(기타)'
        
    if m.startswith('-') or m.startswith('+') or '순살추가' in m_no_space or '순살변경' in m_no_space:
        if '순살' in m_no_space:
            if '메뉴1' in m_no_space or '메뉴2' in m_no_space:
                return '세트순살옵션'
            else:
                return '단품순살옵션'
        else:
            return '제외(기타)'
            
    # 배달, 포장, 홀매출 등 기타 키워드 제외
    if '배달' in m or '포장' in m_no_space or '홀매출' in m_no_space:
        return '제외(기타)'
        
    # 3. 세트 조건 ('순살두마리세트', '취향존중세트', '취향존중순살두마리세트'만 세트로 분류)
    if any(s in m_no_space for s in ['순살두마리세트', '취향존중세트', '취향존중순살두마리세트']):
        return '세트'
        
    # 4. 사이드 판별
    if any(k in m for k in ['사리', '똥집', '치즈볼', '음료', '콜라', '사이다', '튀김', '밥', '햇반', '감자', '떡', '소스', '무', '우동']):
        if not ('우동사리세트' in m_no_space or '똥집세트' in m_no_space or '세트' in m_no_space):
            return '사이드'
        
    # 5. 그 외 치킨 메뉴 및 단품성 세트류는 모두 '단품'으로 처리
    return '단품'

def get_bone_type(raw_menu, menu_type):
    m_no_space = str(raw_menu).replace(' ', '')
    if menu_type in ['세트', '단품']:
        if '안함' in m_no_space:
            return '뼈'
        elif '순살' in m_no_space: