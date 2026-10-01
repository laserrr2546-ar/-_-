import streamlit as st
import pandas as pd

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(page_title="꾸브라꼬 가맹점 손익 계산기", layout="wide")

st.title("🍗 꾸브라꼬 가맹점 손익 분석 시스템")
st.markdown("엑셀 **'가맹점 손익 시트'**의 모든 항목과 자동 계산 로직이 들어있는 대시보드입니다.")

# 탭 구성: 단일 계산기 & 엑셀 파일 대량 분석
tab1, tab2 = st.tabs(["📝 단일 가맹점 손익 계산기", "📁 엑셀 파일 대량 분석"])

# ==========================================
# TAB 1: 단일 가맹점 계산기 (개별 입력)
# ==========================================
with tab1:
    st.subheader("매장별 입력 및 실시간 손익 계산")
    
    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        st.markdown("#### 1. 기본 정보 & 매출(입금)")
        매장명 = st.text_input("매장명", value="김해 내외점")
        월매출 = st.number_input("월 매출 (총매출액)", value=25514200, step=100000)
        
        st.caption("--- [ 플랫폼별 입금액 ] ---")
        배민 = st.number_input("배민 (입금기준)", value=7369084, step=10000)
        요기요 = st.number_input("요기요 (입금기준)", value=1981307, step=10000)
        쿠팡이츠 = st.number_input("쿠팡이츠 (입금기준)", value=6278255, step=10000)
        땡겨요 = st.number_input("땡겨요 (입금기준)", value=266219, step=10000)
        위메프오 = st.number_input("위메프오 (입금기준)", value=163200, step=10000)
        포스매출 = st.number_input("포스매출", value=260300, step=10000)
        기타매출 = st.number_input("기타 (먹깨비, 울산페달, 양산배달 등)", value=769000, step=10000)

    with col_in2:
        st.markdown("#### 2. 물류 비용")
        물류대 = st.number_input("물류대", value=11713698, step=100000)
        
        st.markdown("#### 3. 운영 비용")
        인건비 = st.number_input("인건비", value=2500000, step=100000)
        기름 = st.number_input("기름", value=300000, step=10000)
        음료 = st.number_input("음료", value=200000, step=10000)
        주류 = st.number_input("주류", value=100000, step=10000)

    with col_in3:
        st.markdown("#### 3. 운영 비용 (이어서)")
        월세 = st.number_input("월세", value=800000, step=10000)
        공과금 = st.number_input("공과금", value=150000, step=10000)
        퀵비 = st.number_input("퀵비", value=600000, step=10000)
        포스이용료 = st.number_input("포스이용료", value=30000, step=1000)
        기타잡비 = st.number_input("기타 잡비 (보험·인터넷·정수기 등)", value=200000, step=10000)

    # ------------------------------------------
    # 손익 계산 로직 (엑셀 수식 동일)
    # ------------------------------------------
    입금합계 = 배민 + 요기요 + 쿠팡이츠 + 땡겨요 + 위메프오 + 포스매출 + 기타매출
    입금_마이너스_물류대 = 입금합계 - 물류대
    기타합계_운영비 = 인건비 + 기름 + 음료 + 주류 + 월세 + 공과금 + 퀵비 + 포스이용료 + 기타잡비
    최종금액 = 입금_마이너스_물류대 - 기타합계_운영비

    # 비율 계산 (입금합계 기준 / 월매출 기준)
    수익률 = (최종금액 / 입금합계 * 100) if 입금합계 > 0 else 0.0
    물류비율 = (물류대 / 월매출 * 100) if 월매출 > 0 else 0.0
    인건비율 = (인건비 / 월매출 * 100) if 월매출 > 0 else 0.0

    st.divider()

    # ------------------------------------------
    # 결과 요약 화면
    # ------------------------------------------
    st.subheader(f"📊 [{매장명}] 최종 계산 결과")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("입금 합계", f"{입금합계:,.0f} 원")
    m2.metric("월 매출액", f"{월매출:,.0f} 원")
    m3.metric("기타 합계 (운영비)", f"{기타합계_운영비:,.0f} 원")
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
    with st.expander("📋 상세 계산서 보기"):
        st.write(f"- **입금 합계:** {입금합계:,.0f} 원")
        st.write(f"- **물류대 차감 후 (입금합계 - 물류대):** {입금_마이너스_물류대:,.0f} 원")
        st.write(f"- **운영비용 차감 (기타 합계):** {기타합계_운영비:,.0f} 원")
        st.write(f"- **최종 금액:** {최종금액:,.0f} 원")


# ==========================================
# TAB 2: 엑셀 파일 대량 분석 (가맹점 손익시트 파일 업로드)
# ==========================================
with tab2:
    st.subheader("📂 '가맹점_손익시트.xlsx' 파일 분석")
    uploaded_file = st.file_uploader("손익시트 엑셀 파일을 업로드하세요", type=["xlsx"])

    if uploaded_file is not None:
        try:
            # 엑셀 파일 읽기 (4번째 행이 실제 헤더)
            df = pd.read_excel(uploaded_file, sheet_name="손익 시트", header=3)
            
            # 불필요한 결측열 제거 및 컬럼 정리
            df_clean = df.dropna(how="all").dropna(subset=["매장명"]).copy()
            
            # 숫자형 변환
            num_cols = df_clean.columns.drop(["No.", "매장명"])
            for c in num_cols:
                df_clean[c] = pd.to_numeric(df_clean[c], errors="coerce").fillna(0)

            st.success(f"총 {len(df_clean)}개 매장 데이터를 성공적으로 불러왔습니다.")

            # 주요 요약 지표
            tot_sales = df_clean["월 매출"].sum()
            tot_deposit = df_clean["입금 합계"].sum()
            tot_profit = df_clean["최종 금액"].sum()
            avg_profit_rate = (df_clean["수익률"].mean()) * 100

            sum1, sum2, sum3, sum4 = st.columns(4)
            sum1.metric("전체 가맹점 월매출 총합", f"{tot_sales:,.0f} 원")
            sum2.metric("전체 입금액 총합", f"{tot_deposit:,.0f} 원")
            sum3.metric("전체 최종 순수익 총합", f"{tot_profit:,.0f} 원")
            sum4.metric("평균 수익률", f"{avg_profit_rate:.2f} %")

            st.markdown("---")
            st.markdown("### 📋 가맹점별 손익 현황 데이터표")
            
            # 비율 항목 백분율 표시 포맷팅
            df_display = df_clean.copy()
            df_display["수익률"] = df_display["수익률"].map(lambda x: f"{x*100:.2f}%")
            df_display["물류비율"] = df_display["물류비율"].map(lambda x: f"{x*100:.2f}%")
            df_display["인건비율"] = df_display["인건비율"].map(lambda x: f"{x*100:.2f}%")

            st.dataframe(df_display, use_container_width=True)

        except Exception as e:
            st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    else:
        st.info("👆 상단에서 '가맹점_손익시트.xlsx' 파일을 업로드해 주세요.")