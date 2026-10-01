import streamlit as st
import pandas as pd
import os

# ==========================================
# 1. 페이지 설정 및 엑셀 데이터 불러오기
# ==========================================
st.set_page_config(page_title="꾸브라꼬 가맹점 손익 계산기", layout="wide")

# 앱 실행 시 엑셀 파일을 한 번만 읽어오도록 캐싱 처리 (속도 최적화)
@st.cache_data
def load_excel_data():
    file_path = "가맹점_손익시트.xlsx"
    if not os.path.exists(file_path):
        return None
    
    try:
        # 엑셀의 4번째 행(인덱스 3)이 실제 헤더
        df = pd.read_excel(file_path, sheet_name="손익 시트", header=3)
        # 빈 데이터 행 정리
        df_clean = df.dropna(how="all").dropna(subset=["매장명"]).copy()
        
        # 숫자 계산을 위해 텍스트 혼재 방지(숫자형 변환)
        num_cols = df_clean.columns.drop(["No.", "매장명"])
        for c in num_cols:
            df_clean[c] = pd.to_numeric(df_clean[c], errors="coerce").fillna(0)
        return df_clean
    except Exception as e:
        st.error(f"엑셀 파일을 읽는 중 오류 발생: {e}")
        return None

df = load_excel_data()

# ==========================================
# 2. 메인 대시보드 UI
# ==========================================
st.title("🍗 꾸브라꼬 가맹점 실시간 손익 시뮬레이터")

if df is None or df.empty:
    st.warning("⚠️ 동일한 폴더에 '가맹점_손익시트.xlsx' 파일이 없습니다. 파일을 준비한 뒤 새로고침 해주세요.")
else:
    st.markdown("🔍 **매장을 검색/선택하면 기존 엑셀 데이터가 자동으로 채워집니다.** 값을 직접 수정해 즉각적인 시뮬레이션 결과를 확인하세요.")

    # 매장 목록 리스트 추출
    store_list = df["매장명"].astype(str).tolist()

    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        st.markdown("#### 1. 기본 정보 & 매출(입금)")
        # 검색 가능한 드롭다운 박스 적용
        selected_store = st.selectbox("🏪 매장명 검색/선택", options=store_list)
        
        # 선택된 매장의 엑셀 데이터(Row) 가져오기
        store_data = df[df["매장명"] == selected_store].iloc[0]
        
        # 엑셀에서 가져온 값을 초기값(value)으로 세팅하기 위한 추출 작업
        월매출_val = int(store_data.get("월 매출", 0))
        배민_val = int(store_data.get("배민\n(입금기준)", 0))
        요기요_val = int(store_data.get("요기요\n(입금기준)", 0))
        쿠팡이츠_val = int(store_data.get("쿠팡이츠\n(입금기준)", 0))
        땡겨요_val = int(store_data.get("땡겨요\n(입금기준)", 0))
        위메프오_val = int(store_data.get("위메프오\n(입금기준)", 0))
        포스매출_val = int(store_data.get("포스매출", 0))
        기타매출_val = int(store_data.get("기타\n(먹깨비, 울산페달, 양산배달)", 0))
        
        # 숫자 입력창: 초기값(value)을 엑셀 데이터로 설정 (수정하면 즉시 변수에 반영됨)
        월매출 = st.number_input("월 매출 (총매출액)", value=월매출_val, step=100000)
        
        st.caption("--- [ 플랫폼별 입금액 ] ---")
        배민 = st.number_input("배민 (입금기준)", value=배민_val, step=10000)
        요기요 = st.number_input("요기요 (입금기준)", value=요기요_val, step=10000)
        쿠팡이츠 = st.number_input("쿠팡이츠 (입금기준)", value=쿠팡이츠_val, step=10000)
        땡겨요 = st.number_input("땡겨요 (입금기준)", value=땡겨요_val, step=10000)
        위메프오 = st.number_input("위메프오 (입금기준)", value=위메프오_val, step=10000)
        포스매출 = st.number_input("포스매출", value=포스매출_val, step=10000)
        기타매출 = st.number_input("기타 (먹깨비, 울산페달, 양산배달 등)", value=기타매출_val, step=10000)

    with col_in2:
        st.markdown("#### 2. 물류 비용")
        물류대_val = int(store_data.get("물류대", 0))
        물류대 = st.number_input("물류대", value=물류대_val, step=100000)
        
        st.markdown("#### 3. 운영 비용")
        인건비_val = int(store_data.get("인건비", 0))
        기름_val = int(store_data.get("기름", 0))
        음료_val = int(store_data.get("음료", 0))
        주류_val = int(store_data.get("주류", 0))
        
        인건비 = st.number_input("인건비", value=인건비_val, step=100000)
        기름 = st.number_input("기름", value=기름_val, step=10000)
        음료 = st.number_input("음료", value=음료_val, step=10000)
        주류 = st.number_input("주류", value=주류_val, step=10000)

    with col_in3:
        st.markdown("#### 3. 운영 비용 (이어서)")
        월세_val = int(store_data.get("월세", 0))
        공과금_val = int(store_data.get("공과금", 0))
        퀵비_val = int(store_data.get("퀵비", 0))
        포스이용료_val = int(store_data.get("포스이용료", 0))
        기타잡비_val = int(store_data.get("기타 잡비\n(보험·인터넷·정수기 등)", 0))
        
        월세 = st.number_input("월세", value=월세_val, step=10000)
        공과금 = st.number_input("공과금", value=공과금_val, step=10000)
        퀵비 = 대행료 = st.number_input("퀵비", value=퀵비_val, step=10000)
        포스이용료 = st.number_input("포스이용료", value=포스이용료_val, step=1000)
        기타잡비 = st.number_input("기타 잡비 (보험·인터넷·정수기 등)", value=기타잡비_val, step=10000)


    # ==========================================
    # 3. 실시간 손익 계산 로직 (수정된 값 기반)
    # ==========================================
    입금합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타매출
    입금_마이너스_물류대 = 입금합계 - 물류대
    기타합계_운영비 = 인건비 + 기름 + 음료 + 주류 + 월세 + 공과금 + 퀵비 + 포스이용료 + 기타잡비
    최종금액 = 입금_마이너스_물류대 - 기타합계_운영비

    # 비율 계산 (입금합계 기준 / 월매출 기준)
    수익률 = (최종금액 / 입금합계 * 100) if 입금합계 > 0 else 0.0
    물류비율 = (물류대 / 월매출 * 100) if 월매출 > 0 else 0.0
    인건비율 = (인건비 / 월매출 * 100) if 월매출 > 0 else 0.0

    st.divider()

    # ==========================================
    # 4. 결과 요약 화면
    # ==========================================
    st.subheader(f"📊 [{selected_store}] 실시간 시뮬레이션 결과")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("입금 합계", f"{입금합계:,.0f} 원")
    m2.metric("월 매출액", f"{월매출:,.0f} 원")
    m3.metric("기타 합계 (운영비용 총합)", f"{기타합계_운영비:,.0f} 원")
    m4.metric("💰 최종 순수익 (최종금액)", f"{최종금액:,.0f} 원")

    st.markdown("---")
    
    r1, r2, r3 = st.columns(3)
    with r1:
        st.info(f"**수익률 (입금합계 대비):** {수익률:.2f} %")
    with r2:
        st.warning(f"**물류비율 (월매출 대비):** {물류비율:.2f} %")
    with r3:
        st.error(f"**인건비율 (월매출 대비):** {인건비율:.2f} %")

    # 상세 계산 요약
    with st.expander("📋 상세 수식 확인하기"):
        st.write(f"- **입금 합계:** {입금합계:,.0f} 원")
        st.write(f"- **물류대 차감 후 (입금합계 - 물류대):** {입금_마이너스_물류대:,.0f} 원")
        st.write(f"- **운영비용 차감 (기타 합계):** {기타합계_운영비:,.0f} 원")
        st.write(f"**= 최종 수익:** {최종금액:,.0f} 원")