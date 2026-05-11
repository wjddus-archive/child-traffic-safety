import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 페이지 기본 설정 및 DB 연결
# ==========================================
st.set_page_config(page_title="어린이 교통안전 대시보드", layout="wide")

# 데이터베이스 파일 확인 (mydbdb.db 또는 safety.db)
db_file = "mydbdb.db"
if not os.path.exists(db_file) and not os.path.exists("safety.db"):
    st.error("데이터베이스 파일을 찾을 수 없습니다. 😢 (mydbdb.db 또는 safety.db 파일을 같은 폴더에 넣어주세요!)")
    st.stop()
if os.path.exists("safety.db") and not os.path.exists(db_file):
    db_file = "safety.db"

# 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data(query):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 헤더 영역
st.title("🛡️ 지역별 어린이 교통안전 및 인프라 대시보드")
st.markdown("어린이집 인프라 현황, 교통사고 상관관계, 시간대별 위험도를 종합적으로 분석합니다.")
st.divider()

# 3개의 탭(Tab) 생성
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
        # 확인된 데이터('운영', '미운영')에 맞춰 직관적인 색상 매핑
        color_map = {'운영': '#3498db', '미운영': '#bdc3c7'}
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
        # 데이터가 '운영'으로 확인되었으므로 정확히 일치하는 것만 카운트
        query2_2 = """
            SELECT a.시군구,
                   COUNT(CASE WHEN b.통학차량운영여부 = '운영' THEN 1 END) AS 통학차량_운영수,
                   MAX(a."2024") AS 사고수_2024
            FROM "시군구별 교통사고 통계" a
            LEFT JOIN "어린이집 정보" b ON a.시군구 = b.시군구
            GROUP BY a.시군구
        """
        df2_2 = load_data(query2_2)
        fig2_2 = px.scatter(df2_2, x='통학차량_운영수', y='사고수_2024', text='시군구', 
                            size='사고수_2024', color='사고수_2024', color_continuous_scale='Reds')
        fig2_2.update_traces(textposition='top center')
        st.plotly_chart(fig2_2, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 통학차량 운행 규모가 실제 사고 발생량과 강한 양의 상관관계를 가지는지 분석합니다.
        * 추세선을 벗어나 유독 사고가 많은 지역은 통학차량 외의 다른 위험 요인(예: 불법주차)을 의심해야 합니다.
        """)

    # 2-3. 보육 아동 수 대비 사고 발생률 (막대 차트)
    with col4:
        st.subheader("보육 아동 1,000명당 교통사고 발생률")
        query2_3 = """
            SELECT a.시군구,
                   SUM(b.현원) AS 총_보육아동수,
                   MAX(a."2024") AS 사고수_2024,
                   (CAST(MAX(a."2024") AS FLOAT) / SUM(b.현원)) * 1000 AS 아동1000명당_사고수
            FROM "시군구별 교통사고 통계" a
            JOIN "어린이집 정보" b ON a.시군구 = b.시군구
            GROUP BY a.시군구
            HAVING 총_보육아동수 > 0
            ORDER BY 아동1000명당_사고수 DESC
            LIMIT 10
        """
        df2_3 = load_data(query2_3)
        fig2_3 = px.bar(df2_3.sort_values('아동1000명당_사고수', ascending=True), 
                        x='아동1000명당_사고수', y='시군구', orientation='h', 
                        color='아동1000명당_사고수', color_continuous_scale='YlOrRd')
        st.plotly_chart(fig2_3, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 단순히 사고가 많은 지역이 아니라, **"실제 활동하는 아이들 수 대비 사고가 잦은 진짜 위험 지역"**을 도출합니다.
        * 이 지표가 높다면 해당 지역의 도로 인프라 자체가 보행 어린이에게 매우 열악함을 의미합니다.
        """)


# ==========================================
# [Tab 3] 시간대별 안전 효율 분석
# ==========================================
with tab3:
    st.header("3. 시간대별 안전 효율 분석 (Temporal Efficiency)")
    
    # 3-1. 평일 하원 시간대 집중도 (히트맵) - 정확한 구간 매칭
    st.subheader("오후/하원 시간대 지역별 위험 노출도 (히트맵)")
    
    query3_1 = """
        WITH TotalStats AS (
            SELECT SUM("월요일 사고 수" + "화요일 사고 수" + "수요일 사고 수" + "목요일 사고 수" + "금요일 사고 수") AS 일일총합계 
            FROM "요일별, 시간대별 교통사고 통계 최최종"
        ),
        HourlyStats AS (
            SELECT 시간, 
                   SUM("월요일 사고 수" + "화요일 사고 수" + "수요일 사고 수" + "목요일 사고 수" + "금요일 사고 수") AS 사고합계
            FROM "요일별, 시간대별 교통사고 통계 최최종"
            WHERE 시간 IN ('12시~14시', '14시~16시', '16시~18시', '18시~20시')
            GROUP BY 시간
        )
        SELECT a.시군구, 
               h.시간, 
               ROUND(a."2024" * (CAST(h.사고합계 AS FLOAT) / t.일일총합계), 1) AS 추정사고수
        FROM "시군구별 교통사고 통계" a
        CROSS JOIN HourlyStats h 
        CROSS JOIN TotalStats t
    """
    df3_1 = load_data(query3_1)
    
    if df3_1.empty:
        st.warning("데이터를 불러오지 못했습니다. DB의 시간 데이터 포맷을 다시 확인해주세요!")
    else:
        # 시간대 정렬
        time_order =['12시~14시', '14시~16시', '16시~18시', '18시~20시']
        df3_1['시간'] = pd.Categorical(df3_1['시간'], categories=time_order, ordered=True)
        
        # 피벗 변환 후 히트맵 렌더링
        df_pivot = df3_1.pivot(index='시간', columns='시군구', values='추정사고수')
        fig3_1 = px.imshow(df_pivot, text_auto=True, aspect="auto", color_continuous_scale='OrRd',
                           labels=dict(x="자치구", y="오후 시간대", color="추정사고수"))
        fig3_1.update_yaxes(autorange="reversed") # 시간 순서가 자연스럽게 위에서 아래로 흐르도록
        st.plotly_chart(fig3_1, use_container_width=True)

    st.info("""
    **💡 인사이트**
    * 평일 오후 중 아이들의 이동이 겹치는 **'16시~18시'** 구간이 다른 시간대에 비해 얼마나 위험한지 비교합니다.
    * 색이 가장 짙은 칸(특정 자치구의 16~18시)을 타겟으로 시간제 단속 카메라 및 인력을 집중 배치해야 합니다.
    """)

    col5, col6 = st.columns(2)

    # 3-2. 연도별 사고 감소 추이 (라인 차트)
    with col5:
        st.subheader("연도별 전체 사고 감소 추이")
        query3_2 = """
            SELECT '2020' AS 연도, SUM("2020") AS 전체사고수 FROM "시군구별 교통사고 통계" UNION ALL
            SELECT '2021' AS 연도, SUM("2021") AS 전체사고수 FROM "시군구별 교통사고 통계" UNION ALL
            SELECT '2022' AS 연도, SUM("2022") AS 전체사고수 FROM "시군구별 교통사고 통계" UNION ALL
            SELECT '2023' AS 연도, SUM("2023") AS 전체사고수 FROM "시군구별 교통사고 통계" UNION ALL
            SELECT '2024' AS 연도, SUM("2024") AS 전체사고수 FROM "시군구별 교통사고 통계"
        """
        df3_2 = load_data(query3_2)
        fig3_2 = px.line(df3_2, x='연도', y='전체사고수', markers=True)
        fig3_2.update_traces(line_color='#27ae60', line_width=4, marker_size=10)
        st.plotly_chart(fig3_2, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 지역별 교통안전 정책 시행 이후 연도별로 사고가 실제로 줄고 있는지 거시적으로 확인합니다.
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
        df3_3_melt = df3_3.melt(var_name='요일', value_name='사고수')
        cats =['월', '화', '수', '목', '금', '토', '일']
        df3_3_melt['요일'] = pd.Categorical(df3_3_melt['요일'], categories=cats, ordered=True)
        df3_3_melt = df3_3_melt.sort_values('요일')
        
        fig3_3 = px.bar(df3_3_melt, x='요일', y='사고수', color='사고수', color_continuous_scale='Purples')
        st.plotly_chart(fig3_3, use_container_width=True)
        st.info("""
        **💡 인사이트**
        * 평일(학습일)과 주말의 사고 패턴 차이를 뚜렷하게 분석할 수 있습니다.
        * 주말 사고량이 높다면 거주지 주변(아파트 단지, 공원) 환경 점검이 추가로 필요함을 시사합니다.
        """)
