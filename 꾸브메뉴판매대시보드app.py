import pandas as pd

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
        
    # 3. 사이드 판별 (우동사리세트 등 이름에 '세트'가 들어가더라도 실제로는 사이드나 단품인 경우 우선 차단)
    if '우동사리세트' in m_no_space:
        return '사이드'
        
    if any(k in m for k in ['사리', '똥집', '치즈볼', '음료', '콜라', '사이다', '튀김', '밥', '햇반', '감자', '떡', '소스', '무', '우동']):
        return '사이드'
        
    # 4. 세트 vs 단품 명확히 구분
    if ('두마리' in m_no_space and '세트' in m_no_space) or ('취향존중' in m_no_space and '세트' in m_no_space):
        return '세트'
        
    return '단품'

def get_bone_type(raw_menu, menu_type):
    m_no_space = str(raw_menu).replace(' ', '')
    if menu_type in ['세, 단품', '세트', '단품']: # 일반 단품/세트 판정
        if '안함' in m_no_space:
            return '뼈'
        elif '순살' in m_no_space:
            return '순살'
        else:
            return '뼈'
    return '-'

# -------------------
# 메인 실행 / 데이터프레임 적용 예시
# -------------------
def process_sales_data(df, menu_column_name='메뉴'):
    """
    판매 데이터프레임에 분류 함수들을 적용하여 정제된 컬럼들을 추가하는 함수
    """
    # 1. 메뉴 타입 분류
    df['menu_type'] = df[menu_column_name].apply(get_menu_type)
    
    # 2. 뼈/순살 타입 분류 (menu_type 결과 반영)
    df['bone_type'] = df.apply(lambda row: get_bone_type(row[menu_column_name], row['menu_type']), axis=1)
    
    # 3. 타겟 치킨 메뉴 세부 분류
    df['target_chicken'] = df[menu_column_name].apply(get_target_chicken)
    
    return df

# 테스트용 샘플 데이터 구동부
if __name__ == "__main__":
    sample_data = {
        '메뉴': [
            '소금구이 (순살변경)', 
            '우동사리세트', 
            '취향존중두마리세트 (양념꾸브+소금꾸브)', 
            '170도 후라이드 치킨', 
            '콜라 1.25L', 
            '저당양념구이 (뼈)'
        ]
    }
    
    df_sample = pd.DataFrame(sample_data)
    
    # 함수 적용
    processed_df = process_sales_data(df_sample, menu_column_name='메뉴')
    
    print("=== 분류 결과 출력 ===")
    print(processed_df[['메뉴', 'menu_type', 'bone_type', 'target_chicken']])
