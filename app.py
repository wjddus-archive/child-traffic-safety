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

db_file = "mydbdb.db"
if not os.path.exists(db_file) and not os.path.exists("safety.db"):
    st.error("데이터베이스 파일을 찾을 수 없습니다. 😢 (mydbdb.db 또는 safety.db 파일을 같은 폴더에 넣어주세요!)")
    st.stop()
if os.path.exists("safety.db") and not os.path.exists(db_file):
    db_file = "safety.db"

@st.cache_data
def load_data(query):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.title("🛡️ 지역별 어린이 교통안전 및 인프라 대시보드")
st.markdown("어린이집 인프라 현황, 교통사고 상관관계, 시간대별 위험도를 종합적으로 분석합니다.")
st.divider()

tab1, tab2, tab3 = st.tabs([
    "🏢 1. 이용 대상 및 인프라 분석", 
    "⚠️ 2. 지역 및 사고 상관관계 분석", 
    "⏰ 3. 시간대별 안전 효율 분석"
])

# ==========================================
# [Tab 1] 이용 대상 및 인프라 분석 (인사이트 생략)
# ==========================================
with tab1:
    st.header("1. 이용 대상 및 인프라 분석 (Infrastructure)")
    col1, col2 = st.columns(2)
    
    # 1-1. 어린이집 유형별 비중
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

    # 1-2. 통학차량 운영 현황
    with col2:
        st.subheader("통학차량 운영 현황")
        query1_2 = """
            SELECT 통학차량운영여부, COUNT(*) AS 어린이집_수
            FROM "어린이집 정보"
            GROUP BY 통학차량운영여부
        """
        df1_2 = load_data(query1_2)
        color_map = {'운영': '#3498db', '미운영': '#bdc3c7'}
        fig1_2 = px.pie(df1_2, values='어린이집_수', names='통학차량운영여부', 
                        color='통학차량운영여부', color_discrete_map=color_map)
        st.plotly_chart(fig1_2, use_container_width=True)

    # 1-3. 지역별 인프라 밀집도
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
    
    # 2-1. 자치구별 사고 위험도
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
    
    # [사용자 작성 인사이트 1 적용]
    st.info("""
    **💡 1. 인프라 규모와 실제 사고 발생의 '불균형' 분석**
    * **의미 도출:** 어린이집 수(공급 인프라)와 실제 사고 수(발생 현황)가 비례하지 않는 구간에 주목해야 합니다.
    * **고위험 자치구 식별:** 송파구와 강남구는 시설 수 대비 사고 곡선이 매우 높게 형성되어 있습니다. 이는 단순히 시설이 많아서 사고가 나는 것이 아니라, 해당 지역의 교통 환경 자체가 타 구에 비해 위험함을 시사합니다.
    * **관리 효율 지역:** 반면, 노원구나 강서구는 시설 수는 많지만 사고 곡선은 상대적으로 완만하게 내려가는 모습을 보이며 비교적 안전하게 관리되고 있음을 알 수 있습니다.
    """)

    st.divider()

    col3, col4 = st.columns(2)
    
    # 2-2. 차량 운영 시설 대비 사고량
    with col3:
        st.subheader("차량 운영 시설 대비 사고량")
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

    # 2-3. 보육 아동 수 대비 사고 발생률
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

    #[사용자 작성 인사이트 2 적용 - 두 차트를 종합하여 설명]
    st.info("""
    **💡 2. 사고 유발 요인의 다각화 (차량 운영 vs 보육 아동)**
    * **통학 차량의 영향력:** 산점도에서 추세선을 크게 벗어나 상단에 위치한 강남구, 서초구 등은 통학 차량 운영 외에도 '불법 주정차'나 '유동 차량 밀집' 등 외부 위험 요인이 사고에 더 큰 영향을 미치고 있을 가능성이 큽니다.
    * **실질적 위험도 (아동 1,000명당):** 절대적인 사고 건수보다 무서운 수치는 밀도입니다. 강남구와 양천구는 활동하는 아이들 수 대비 사고 비중이 가장 높습니다. 이는 보행로 분리 미흡 등 도로 인프라의 근본적인 취약성을 나타냅니다.
    """)


# ==========================================
# [Tab 3] 시간대별 안전 효율 분석
# ==========================================
with tab3:
    st.header("3. 시간대별 안전 효율 분석 (Temporal Efficiency)")
    
    # 3-1. 평일 하원 시간대 집중도 (히트맵)
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
        time_order =['12시~14시', '14시~16시', '16시~18시', '18시~20시']
        df3_1['시간'] = pd.Categorical(df3_1['시간'], categories=time_order, ordered=True)
        
        df_pivot = df3_1.pivot(index='시간', columns='시군구', values='추정사고수')
        fig3_1 = px.imshow(df_pivot, text_auto=True, aspect="auto", color_continuous_scale='OrRd',
                           labels=dict(x="자치구", y="오후 시간대", color="추정사고수"))
        fig3_1.update_yaxes(autorange="reversed")
        st.plotly_chart(fig3_1, use_container_width=True)

    # [사용자 작성 인사이트 3 적용]
    st.info("""
    **💡 3. 시간적 타겟팅: '마의 16~18시'**
    * **집중 행정의 필요성:** 모든 자치구에서 16~18시 구간이 가장 짙은 색을 띱니다.
    * **피크 타임 분석:** 특히 송파(26.8), 강남(23.7) 지역의 이 시간대 수치는 타 지역의 평소 시간대보다 몇 배나 높습니다.
    * **대책 도출:** 인력과 예산을 24시간 분산하기보다, 해당 시간대(16~18시)에 단속 카메라 가동 및 안전 요원 배치를 집중하는 것이 가장 효율적인 사고 예방책임을 보여줍니다.
    """)

    st.divider()

    col5, col6 = st.columns(2)

    # 3-2. 연도별 사고 감소 추이
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

    # 3-3. 요일별 사고 분포
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

    #[사용자 작성 인사이트 4 적용 - 하단에 가로로 넓게 배치]
    st.info("""
    **💡 4. 거시적 추세와 요일별 특성**
    * **정책의 실효성 확인:** 2022년 정점을 찍고 감소세로 돌아선 그래프는 최근의 어린이 보호구역 강화 정책 등이 거시적으로는 효과를 거두고 있음을 입증합니다.
    * **주말 사고의 역설:** 평일(학습일)보다 토요일에 사고가 급증하는 패턴은 시사하는 바가 큽니다.
    * **의미:** 사고가 어린이집 주변뿐만 아니라 주말 가족 단위 활동 범위(공원, 아파트 단지 내, 상업지구)로 확장되고 있다는 뜻입니다.
    * **확장된 안전망:** 평일 등하굣길 안전 중심에서 주말 주거지 주변 환경 점검으로 정책의 범위를 넓혀야 함을 시사합니다.
    """)
