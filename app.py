import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="어린이 교통안전 대시보드", layout="wide")

# ==========================================
# 2. 데이터베이스 연결 및 에러 처리
# ==========================================
db_file = "mydbdb.db"
if not os.path.exists(db_file) and not os.path.exists("safety.db"):
    st.error("데이터베이스 파일을 찾을 수 없습니다. 😢 (mydbdb.db 또는 safety.db 파일을 같은 폴더에 넣어주세요!)")
    st.stop()

if os.path.exists("safety.db") and not os.path.exists(db_file):
    db_file = "safety.db"

# ==========================================
# 3. 데이터 로드 함수
# ==========================================
@st.cache_data
def load_data(query):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 헤더
st.title("🛡️ 지역별 어린이 교통안전 및 인프라 대시보드")
st.markdown("어린이집 인프라 현황, 교통사고 상관관계, 시간대별 위험도를 종합적으로 분석합니다.")
st.divider()

# 3개의 카테고리를 탭(Tab)으로 나누어 깔끔하게 배치합니다.
tab1, tab2, tab3 = st.tabs([
    "🏢 1. 이용 대상 및 인프라 분석", 
    "⚠️ 2. 지역 및 사고 상관관계 분석", 
    "⏰ 3. 시간대별 안전 효율 분석"
])

# ==========================================
# [Tab 1] 이용 대상 및 인프라 분석
# ==========================================
with tab1:
    st.header("1. 이용 대상 및 인프라 분석 (Infrastructure)")
    col1, col2 = st.columns(2)
    
    # 1-1. 어린이집 유형별 비중 (도넛 차트)
    with col1:
        st.subheader("어린이집 유형별 비중")
        query1_1 = """
            SELECT 어린이집유형, COUNT(*) AS 어린이집_수
            FROM "어린이집 정보"
            GROUP BY 어린이집유형
        """
        df1_1 = load_data(query1_1)
        fig1_1 = px.pie(df1_1, values='어린이집_수', names='어린이집유형', hole=0.4, 
                        color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig1_1, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 해당 지역의 보육 시설이 국공립 위주인지, 민간/가정 위주인지 한눈에 파악할 수 있습니다.
        * 운영 주체별로 안전 관리 책임 소재가 다르므로, 맞춤형 안전 교육 타겟팅에 유용합니다.
        """)

    # 1-2. 통학차량 운영 현황 (파이 차트)
    with col2:
        st.subheader("통학차량 운영 현황")
        query1_2 = """
            SELECT 통학차량운영여부, COUNT(*) AS 어린이집_수
            FROM "어린이집 정보"
            GROUP BY 통학차량운영여부
        """
        df1_2 = load_data(query1_2)
        # Y/N 직관성을 위해 색상 지정
        color_map = {'Y': '#3498db', 'N': '#bdc3c7'}
        fig1_2 = px.pie(df1_2, values='어린이집_수', names='통학차량운영여부', 
                        color='통학차량운영여부', color_discrete_map=color_map)
        st.plotly_chart(fig1_2, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 통학차량을 운영하는 시설의 비율을 통해 잠재적인 차량 이동 위험 요인을 가늠합니다.
        * 비율이 높다면 어린이 승하차 구역(Drop-off Zone) 정비 예산 편성이 시급함을 의미합니다.
        """)

    # 1-3. 지역별 인프라 밀집도 (가로 막대 차트)
    st.subheader("지역별 인프라 밀집도 (어린이집 수)")
    query1_3 = """
        SELECT a.시군구, COUNT(b.어린이집명) AS 어린이집_수
        FROM "시군구별 교통사고 통계" a
        LEFT JOIN "어린이집 정보" b ON a.시군구 = b.시군구
        GROUP BY a.시군구
        ORDER BY 어린이집_수 ASC
    """
    df1_3 = load_data(query1_3)
    fig1_3 = px.bar(df1_3, x='어린이집_수', y='시군구', orientation='h', 
                    color='어린이집_수', color_continuous_scale='Blues')
    st.plotly_chart(fig1_3, use_container_width=True)


# ==========================================
# [Tab 2] 지역 및 사고 상관관계 분석
# ==========================================
with tab2:
    st.header("2. 지역 및 사고 상관관계 분석 (Location & Risk)")
    
    # 2-1. 자치구별 사고 위험도 (이중 축 막대 차트)
    st.subheader("자치구별 사고 위험도 (2024년 기준)")
    query2_1 = """
        SELECT a.시군구, 
               MAX(a."2024") AS 사고수_2024, 
               COUNT(b.어린이집명) AS 어린이집_수
        FROM "시군구별 교통사고 통계" a
        LEFT JOIN "어린이집 정보" b ON a.시군구 = b.시군구
        GROUP BY a.시군구
        ORDER BY 사고수_2024 DESC
    """
    df2_1 = load_data(query2_1)
    fig2_1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2_1.add_trace(go.Bar(x=df2_1['시군구'], y=df2_1['어린이집_수'], name="어린이집 수", marker_color='#95a5a6'), secondary_y=False)
    fig2_1.add_trace(go.Scatter(x=df2_1['시군구'], y=df2_1['사고수_2024'], name="2024년 사고 수", mode='lines+markers', line=dict(color='#e74c3c', width=3)), secondary_y=True)
    st.plotly_chart(fig2_1, use_container_width=True)
    st.info("""
    **💡 인사이트**
    * 어린이집 인프라 규모(막대) 대비 실제 교통사고 발생 수(선)의 불균형을 확인합니다.
    * 어린이집은 많은데 사고 빈도가 비정상적으로 높은 '고위험 자치구'를 즉각 식별할 수 있습니다.
    """)

    col3, col4 = st.columns(2)
    
    # 2-2. 차량 운영 시설 대비 사고량 (산점도)
    with col3:
        st.subheader("차량 운영 시설 대비 사고량")
        query2_2 = """
            SELECT a.시군구,
                   COUNT(CASE WHEN b.통학차량운영여부 = 'Y' THEN 1 END) AS 통학차량_운영수,
                   MAX(a."2024") AS 사고수_2024
            FROM "시군구별 교통사고 통계" a
            LEFT JOIN "어린이집 정보" b ON a.시군구 = b.시군구
            GROUP BY a.시군구
        """
        df2_2 = load_data(query2_2)
        fig2_2 = px.scatter(df2_2, x='통학차량_운영수', y='사고수_2024', text='시군구', size='사고수_2024', color='사고수_2024', color_continuous_scale='Reds')
        fig2_2.update_traces(textposition='top center')
        st.plotly_chart(fig2_2, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 통학차량 운행 규모가 실제 사고 발생량과 강한 양의 상관관계를 가지는지 분석합니다.
        * 추세선을 벗어나 유독 사고가 많은 지역은 통학차량 외의 다른 위험 요인(예: 불법주차)을 의심해야 합니다.
        """)

    # 2-3. 운영 현황별 수용력 (막대 차트)
    with col4:
        st.subheader("운영 현황별 수용력 (현원 합계)")
        query2_3 = """
            SELECT 운영현황, SUM(현원) AS 총_현원
            FROM "어린이집 정보"
            GROUP BY 운영현황
            ORDER BY 총_현원 DESC
        """
        df2_3 = load_data(query2_3)
        fig2_3 = px.bar(df2_3, x='운영현황', y='총_현원', color='운영현황')
        st.plotly_chart(fig2_3, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 정상 운영, 휴원 등 상태에 따른 실제 현원(보육 인구)의 규모를 파악합니다.
        * 통학을 위해 실제로 도로를 이용하는 활동적인 어린이 인구수를 산출하는 기준이 됩니다.
        """)


# ==========================================
# [Tab 3] 시간대별 안전 효율 분석
# ==========================================
with tab3:
    st.header("3. 시간대별 안전 효율 분석 (Temporal Efficiency)")
    
    # 3-1. 평일 하원 시간대 집중도 (히트맵)
    st.subheader("평일 하원 시간대(16~18시) 지역별 위험 노출도 (히트맵)")
    # 멘토의 팁: 세번째 테이블에 지역 구분이 없으므로 전국 하원 시간대 비율을 구해 시군구 총 사고수에 곱하는 Cross Join 방식을 썼습니다.
    query3_1 = """
        WITH HourlyRatio AS (
            -- 1. 시간대별 사고 비율 계산
            SELECT 시간, 
                   CAST(SUM("월요일 사고 수" + "화요일 사고 수" + "수요일 사고 수" + "목요일 사고 수" + "금요일 사고 수") AS FLOAT) 
                   / SUM(SUM("월요일 사고 수" + "화요일 사고 수" + "수요일 사고 수" + "목요일 사고 수" + "금요일 사고 수")) OVER() AS 비율
            FROM "요일별, 시간대별 교통사고 통계 최최종"
            WHERE 시간 IN ('16시', '17시', '18시') AND 년도 = 2024
            GROUP BY 시간
        )
        -- 2. 시군구 사고수(2024)에 시간대별 비율을 곱해 추정치 생성
        SELECT a.시군구, h.시간, ROUND(a."2024" * h.비율, 1) AS 추정사고수
        FROM "시군구별 교통사고 통계" a
        CROSS JOIN HourlyRatio h
    """
    df3_1 = load_data(query3_1)
    fig3_1 = px.density_heatmap(df3_1, x='시군구', y='시간', z='추정사고수', 
                                histfunc='sum', color_continuous_scale='OrRd',
                                title="지역별 x 시간대별 하원시간 사고 추정 히트맵")
    st.plotly_chart(fig3_1, use_container_width=True)
    st.info("""
    **💡 인사이트**
    * 등하원 피크 시간대(16시, 17시, 18시) 중 어느 시간, 어느 지역의 위험 노출도가 가장 짙은지(붉은색) 직관적으로 시각화합니다.
    * 색이 짙은 시간대와 자치구를 타겟으로 시간제 단속 카메라 및 교통 지도 인력을 집중 배치할 수 있습니다.
    """)

    col5, col6 = st.columns(2)

    # 3-2. 연도별 사고 감소 추이 (라인 차트)
    with col5:
        st.subheader("연도별 전체 사고 감소 추이")
        # 열(Column)로 된 연도 데이터를 행(Row)으로 풀어주는 언피벗(Unpivot) 형태의 쿼리입니다.
        query3_2 = """
            SELECT '2020' AS 연도, SUM("2020") AS 전체사고수 FROM "시군구별 교통사고 통계" UNION ALL
            SELECT '2021' AS 연도, SUM("2021") AS 전체사고수 FROM "시군구별 교통사고 통계" UNION ALL
            SELECT '2022' AS 연도, SUM("2022") AS 전체사고수 FROM "시군구별 교통사고 통계" UNION ALL
            SELECT '2023' AS 연도, SUM("2023") AS 전체사고수 FROM "시군구별 교통사고 통계" UNION ALL
            SELECT '2024' AS 연도, SUM("2024") AS 전체사고수 FROM "시군구별 교통사고 통계"
        """
        df3_2 = load_data(query3_2)
        fig3_2 = px.line(df3_2, x='연도', y='전체사고수', markers=True, line_shape='spline')
        fig3_2.update_traces(line_color='#27ae60', line_width=4, marker_size=10)
        st.plotly_chart(fig3_2, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 지역별 교통안전 정책(스쿨존 단속 카메라 의무화 등) 시행 이후 연도별로 사고가 실제로 줄고 있는지 거시적으로 확인합니다.
        """)

    # 3-3. 요일별 사고 분포 (막대 차트)
    with col6:
        st.subheader("요일별 사고 분포")
        query3_3 = """
            SELECT 
                SUM("월요일 사고 수") AS 월, SUM("화요일 사고 수") AS 화,
                SUM("수요일 사고 수") AS 수, SUM("목요일 사고 수") AS 목,
                SUM("금요일 사고 수") AS 금, SUM("토요일 사고 수") AS 토,
                SUM("일요일 사고 수") AS 일
            FROM "요일별, 시간대별 교통사고 통계 최최종"
        """
        df3_3 = load_data(query3_3)
        # Pandas의 melt 함수를 이용해 가로 데이터를 세로로 변환합니다. (파이썬 데이터 핸들링 팁!)
        df3_3_melt = df3_3.melt(var_name='요일', value_name='사고수')
        # 요일 순서 정렬
        cats =['월', '화', '수', '목', '금', '토', '일']
        df3_3_melt['요일'] = pd.Categorical(df3_3_melt['요일'], categories=cats, ordered=True)
        df3_3_melt = df3_3_melt.sort_values('요일')
        
        fig3_3 = px.bar(df3_3_melt, x='요일', y='사고수', color='사고수', color_continuous_scale='Purples')
        st.plotly_chart(fig3_3, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 평일(학습일)과 주말의 사고 패턴 차이를 뚜렷하게 분석할 수 있습니다.
        * 주말 사고량이 예상외로 높다면 거주지 주변(공원, 아파트 단지)의 교통 환경 점검이 추가로 필요함을 시사합니다.
        """)
