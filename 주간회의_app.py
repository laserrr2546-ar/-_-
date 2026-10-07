import streamlit as st
import pandas as pd
import re
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="꾸브라꼬 매출 분석 대시보드", layout="wide")

@st.cache_data
def load_and_process_data(uploaded_file):
    df = pd.read_excel(uploaded_file, header=1)
    
    # 1. 총계/합계/소계 행 제거
    data = df[~df["일자"].astype(str).str.contains("합계|소계|총계", na=False)].copy()
    
    # 2. 날짜 파싱 (2026년 기준)
    def parse_date(val):
        if pd.isna(val):
            return None
        s = str(val).strip()
        m = re.search(r'(\d+)월\s*(\d+)일', s)
        if m:
            return datetime(2026, int(m.group(1)), int(m.group(2)))
        return None

    data["DT"] = data["일자"].apply(parse_date)
    data = data.dropna(subset=["DT"])

    data["Year"] = data["DT"].dt.year
    data["IsoWeek"] = data["DT"].dt.isocalendar().week

    # 3. 주차명 라벨링
    def get_week_label(row):
        dt = row["DT"]
        start_of_week = dt - pd.Timedelta(days=dt.weekday())
        end_of_week = start_of_week + pd.Timedelta(days=6)
        return f"W{row['IsoWeek']:02d} ({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')})"

    data["주차명"] = data.apply(get_week_label, axis=1)

    # 4. 실매출 계산 = 판매금액 - 채널배달료(매출제외)
    data["판매금액_val"] = pd.to_numeric(data["판매금액"], errors="coerce").fillna(0)
    data["배달료_val"] = pd.to_numeric(data["채널배달료(매출제외)"], errors="coerce").fillna(0)
    data["실매출"] = data["판매금액_val"] - data["배달료_val"]

    # 5. 매장명 기반 지역 및 권역 자동 추출
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
            if token in ["서울", "경기", "인천", "부산", "울산", "대구", "광주", "대전", "강원", "제주", "충남", "충북", "경남", "경북", "전남", "전북"]:
                return token
        return "기타"

    def get_area(region):
        if region in ["서울", "경기", "인천", "대전", "강원", "충청(충남/충북)", "충남", "충북"]:
            return "수도권"
        if region in ["부산", "울산", "대구", "경상(경남/경북)", "경남", "경북"]:
            return "영남권"
        if region in ["광주", "전라(전남/전북)", "전남", "전북"]:
            return "호남권"
        if region == "제주":
            return "제주권"
        return "기타"

    data["지역"] = data["매장명"].apply(get_region)
    data["권역"] = data["지역"].apply(get_area)
    
    return data

# 대시보드 타이틀
st.title("📊 매장별/주차별 매출 분석 대시보드")

# 파일 업로드 컨트롤러
file = st.sidebar.file_uploader("기간별 매출분석 엑셀 파일 업로드", type=["xlsx", "xls"])

if file is not None:
    data = load_and_process_data(file)
    
    # 사이드바 필터
    st.sidebar.header("🔍 필터 옵션")
    
    # 코드가 잘리지 않도록 멀티셀렉트 옵션을 줄바꿈했습니다.
    selected_weeks = st.sidebar.multiselect(
        "주차 선택", 
        options=sorted(data["주차명"].unique()), 
        default=sorted(data["주차명"].unique())
    )
    
    selected_areas = st.sidebar.multiselect(
        "권역 선택", 
        options=sorted(data["권역"].unique()), 
        default=sorted(data["권역"].unique())
    )
    
    filtered_data = data[(data["주차명"].isin(selected_weeks)) & (data["권역"].isin(selected_areas))]
    
    # 핵심 지표 KPI
    col1, col2, col3, col4 = st.columns(4)
    total_sales = filtered_data["실매출"].sum()
    avg_sales = filtered_data["실매출"].mean()
    total_stores = filtered_data["매장명"].nunique()
    total_records = len(filtered_data)
    
    col1.metric("총 실매출", f"{total_sales:,.0f} 원")
    col2.metric("건당 평균 실매출", f"{avg_sales:,.0f} 원")
    col3.metric("운영 매장 수", f"{total_stores:,} 개")
    col4.metric("총 매출 건수", f"{total_records:,} 건")
    
    st.markdown("---")
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["🗓️ 주차별 분석", "🏪 매장별 분석", "🗺️ 권역/지역별 분석", "📄 상세 데이터"])
    
    # [탭 1] 주차별 분석
    with tab1:
        st.subheader("주차별 매출 요약")
        weekly_summary = filtered_data.groupby("주차명")["실매출"].agg(["sum", "mean", "count"]).reset_index()
        weekly_summary.columns = ["주차명", "주간 총매출", "건당 평균매출", "매출 발생 건수"]
        
        total_sum = weekly_summary["주간 총매출"].sum()
        weekly_summary["매출 비중(%)"] = (weekly_summary["주간 총매출"] / total_sum * 100) if total_sum > 0 else 0
            
        st.dataframe(weekly_summary.style.format({
            "주간 총매출": "{:,.0f}원",
            "건당 평균매출": "{:,.0f}원",
            "매출 발생 건수": "{:,}건",
            "매출 비중(%)": "{:.2f}%"
        }), use_container_width=True)
        
        fig_week = px.bar(weekly_summary, x="주차명", y="주간 총매출", text_auto=",", title="주차별 실매출 비교")
        st.plotly_chart(fig_week, use_container_width=True)
        
    # [탭 2] 매장별 분석 (주차별 차이 및 휴무일)
    with tab2:
        st.subheader("주차별 매출 비교 및 휴무일 현황")
        
        # 주차별 전체 일수 계산 (해당 주차에 데이터가 존재하는 날짜 수)
        week_days_total = filtered_data.groupby('IsoWeek')['DT'].nunique().to_dict()
        weeks = sorted(filtered_data['IsoWeek'].unique())
        
        if len(weeks) == 0:
            st.warning("선택된 데이터가 없습니다.")
        else:
            # 1. 주차별 매출 피벗
            sales_pivot = filtered_data.pivot_table(
                index=['매장명', '권역', '지역'], 
                columns='IsoWeek', 
                values='실매출', 
                aggfunc='sum', 
                fill_value=0
            )
            sales_pivot.columns = [f"{col}주차 매출" for col in sales_pivot.columns]
            
            # 2. 주차별 영업일수 피벗 (매출이 발생한 고유 날짜 수)
            days_pivot = filtered_data.pivot_table(
                index=['매장명', '권역', '지역'], 
                columns='IsoWeek', 
                values='DT', 
                aggfunc='nunique', 
                fill_value=0
            )
            
            # 3. 휴무일수 계산 (해당 주차의 전체 일수 - 매장 영업일수)
            closed_pivot = pd.DataFrame(index=days_pivot.index)
            for col in days_pivot.columns:
                closed_pivot[f"{col}주차 휴무일"] = week_days_total[col] - days_pivot[col]
                
            # 데이터 병합
            store_summary = pd.concat([sales_pivot, closed_pivot], axis=1).reset_index()
            
            # 포맷팅 설정
            format_dict = {}
            for col in sales_pivot.columns:
                format_dict[col] = "{:,.0f}원"
            for col in closed_pivot.columns:
                format_dict[col] = "{:,}일"
                
            # 4. 최근 2주 매출 증감액 계산
            if len(weeks) >= 2:
                curr_wk = weeks[-1]
                prev_wk = weeks[-2]
                store_summary['매출 증감액(최근2주)'] = store_summary[f"{curr_wk}주차 매출"] - store_summary[f"{prev_wk}주차 매출"]
                format_dict['매출 증감액(최근2주)'] = "{:,.0f}원"
                store_summary = store_summary.sort_values(by=f"{curr_wk}주차 매출", ascending=False).reset_index(drop=True)
            else:
                store_summary = store_summary.sort_values(by=f"{weeks[0]}주차 매출", ascending=False).reset_index(drop=True)

            # 검색 기능
            search_query = st.text_input("🔍 특정 매장 검색", placeholder="조회할 매장명을 입력하세요 (예: 부산 정관점)")
            
            if search_query:
                display_data = store_summary[store_summary["매장명"].str.contains(search_query, na=False)]
                st.markdown(f"**'{search_query}'** 검색 결과: {len(display_data)}건")
            else:
                display_data = store_summary
                
            # 표시할 컬럼 순서 정리
            base_cols = ["매장명", "권역", "지역"]
            sales_cols = [f"{w}주차 매출" for w in weeks]
            closed_cols = [f"{w}주차 휴무일" for w in weeks]
            
            final_cols = base_cols + sales_cols
            if len(weeks) >= 2:
                final_cols.append("매출 증감액(최근2주)")
            final_cols += closed_cols
            
            display_data = display_data[final_cols]
            
            # 차트 (비교 차트)
            chart_data = display_data if search_query else display_data.head(20)
            
            if len(chart_data) > 0 and len(weeks) >= 2:
                curr_col = f"{curr_wk}주차 매출"
                prev_col = f"{prev_wk}주차 매출"
                
                # 차트를 그리기 위해 구조 변경 (Melt)
                chart_melted = chart_data.melt(
                    id_vars=["매장명"], 
                    value_vars=[prev_col, curr_col], 
                    var_name="주차", 
                    value_name="매출액"
                )
                
                chart_title = "검색된 매장 주간 매출 비교" if search_query else "상위 20개 매장 주간 매출 비교"
                fig_store = px.bar(chart_melted, x="매출액", y="매장명", color="주차", barmode="group", orientation="h", title=chart_title)
                fig_store.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_store, use_container_width=True)
                
            elif len(chart_data) > 0 and len(weeks) == 1:
                col_name = f"{weeks[0]}주차 매출"
                chart_title = "검색된 매장 주간 매출" if search_query else "상위 20개 매장 주간 매출"
                fig_store = px.bar(chart_data, x=col_name, y="매장명", orientation="h", title=chart_title)
                fig_store.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_store, use_container_width=True)
            
            # 최종 테이블 출력
            st.dataframe(display_data.style.format(format_dict), use_container_width=True)

    # [탭 3] 권역/지역별 분석
    with tab3:
        st.subheader("권역 및 지역별 실매출 분포")
        col_a, col_b = st.columns(2)
        
        area_summary = filtered_data.groupby("권역", as_index=False).agg(
            총매출=("실매출", "sum"),
            매장수=("매장명", "nunique")
        ).sort_values(by="총매출", ascending=False)
        
        region_summary = filtered_data.groupby(["권역", "지역"], as_index=False).agg(
            총매출=("실매출", "sum"),
            매장수=("매장명", "nunique")
        ).sort_values(by="총매출", ascending=False)
        
        with col_a:
            fig_area = px.pie(area_summary, values="총매출", names="권역", title="권역별 실매출 비중", hole=0.4)
            st.plotly_chart(fig_area, use_container_width=True)
            
        with col_b:
            fig_region = px.bar(region_summary, x="지역", y="총매출", color="권역", title="지역별 총 실매출 현황")
            st.plotly_chart(fig_region, use_container_width=True)
            
        st.dataframe(region_summary.style.format({
            "총매출": "{:,.0f}원",
            "매장수": "{:,}개"
        }), use_container_width=True)

    # [탭 4] 상세 데이터
    with tab4:
        st.subheader("전체 원본/필터링 데이터 목록")
        st.dataframe(filtered_data[["일자", "주차명", "권역", "지역", "매장명", "판매금액", "채널배달료(매출제외)", "실매출"]], use_container_width=True)

else:
    st.info("👈 왼쪽 사이드바에서 엑셀 파일(.xlsx)을 업로드해주세요.")