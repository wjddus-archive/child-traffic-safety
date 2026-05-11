import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 페이지 설정 (기본 UI로 깔끔하게 유지)
# ==========================================
st.set_page_config(page_title="공공데이터 안전 대시보드", layout="wide")

# ==========================================
# 2. 데이터베이스 연결 및 에러 처리
# ==========================================
db_file = "mydbdb.db"
# safety.db나 mydbdb.db 파일이 없으면 에러 메시지 출력 후 실행 중단
if not os.path.exists(db_file) and not os.path.exists("safety.db"):
    st.error("데이터베이스 파일을 찾을 수 없습니다. 😢 (mydbdb.db 또는 safety.db 파일을 같은 폴더에 넣어주세요!)")
    st.stop()

# 실제 파일 이름에 맞춰서 db_file 변수 설정
if os.path.exists("safety.db") and not os.path.exists(db_file):
    db_file = "safety.db"

# ==========================================
# 3. 데이터 로드 함수 (모듈화)
# ==========================================
@st.cache_data
def load_data(query):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 헤더 영역
st.title("🛡️ 우리 동네 어린이 안전 대시보드")
st.markdown("시군구별 어린이집 데이터와 교통사고 통계를 분석한 대시보드입니다.")
st.divider()

# ==========================================
# 4. 차트 1: 지역별 통학차량 및 사고 현황
# ==========================================
st.header("1. 지역별 통학차량 운영 및 교통사고 현황")

query1 = """
    SELECT 
        a.시군구, 
        COUNT(CASE WHEN b.통학차량운영여부 = 'Y' THEN 1 END) AS 통학차량_운영_어린이집수,
        MAX(a."2024") AS "2024년_사고수"
    FROM "시군구별 교통사고 통계" a
    LEFT JOIN "어린이집 정보" b ON a.시군구 = b.시군구
    GROUP BY a.시군구
    ORDER BY "2024년_사고수" DESC
"""
df1 = load_data(query1)

# ① 시각화 (이중 축 차트)
fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(go.Bar(x=df1['시군구'], y=df1['통학차량_운영_어린이집수'], name="통학차량 운영 수", marker_color='#3498db'), secondary_y=False)
fig1.add_trace(go.Scatter(x=df1['시군구'], y=df1['2024년_사고수'], name="2024년 사고 수", mode='lines+markers', line=dict(color='#e74c3c', width=3)), secondary_y=True)
fig1.update_layout(title_text="시군구별 통학차량 어린이집 수 vs 교통사고 수 (2024)")
st.plotly_chart(fig1, use_container_width=True)

# ② 사용한 SQL 및 ③ 분석 인사이트
with st.expander("📝 SQL 쿼리 및 💡 분석 인사이트 보기"):
    st.code(query1, language="sql")
    st.info("""
    * 통학차량을 많이 운영하는 지역일수록 교통사고 발생 건수와 비례하는지 패턴을 파악할 수 있습니다.
    * 통학차량은 많으나 사고 수가 적은 자치구는 교통안전 관리가 우수하게 이루어지고 있을 확률이 높습니다.
    """)

st.divider()

# ==========================================
# 5. 차트 2: 어린이집 현원율과 사고 위험도
# ==========================================
st.header("2. 어린이집 정원 대비 현원율과 사고 위험도")

query2 = """
    SELECT 
        a.시군구,
        AVG(CAST(b.현원 AS FLOAT) / b.정원) * 100 AS 평균_현원율,
        MAX(a."2024") AS "2024년_사고수",
        COUNT(b.어린이집명) AS 어린이집_수
    FROM "시군구별 교통사고 통계" a
    JOIN "어린이집 정보" b ON a.시군구 = b.시군구
    WHERE b.정원 > 0
    GROUP BY a.시군구
"""
df2 = load_data(query2)

# ① 시각화 (버블 차트)
fig2 = px.scatter(df2, x="평균_현원율", y="2024년_사고수", size="어린이집_수", color="시군구",
                  hover_name="시군구", size_max=40, title="자치구별 현원율 vs 사고 수 (원의 크기: 어린이집 수)")
st.plotly_chart(fig2, use_container_width=True)

with st.expander("📝 SQL 쿼리 및 💡 분석 인사이트 보기"):
    st.code(query2, language="sql")
    st.info("""
    * 보육 밀집도(현원율)가 높은 지역이 통행량이 많아져 사고 건수도 높은지 상관관계를 점검할 수 있습니다.
    * 우상단에 위치한 자치구(현원율도 높고 사고도 많은 곳)는 우선적인 어린이 보호구역 점검이 필요합니다.
    """)

st.divider()

# ==========================================
# 6. 차트 3: 평일 하원 시간대 사고 비중 분석 (에러 해결!)
# ==========================================
st.header("3. 평일 하원 시간대(16시~18시) 사고 취약 상위 10개 지역 추정")

# 멘토의 팁: 
# 세 번째 테이블에 '시군구'가 없으므로, WITH문을 사용해 2024년 데이터를 기준으로 '년도'를 매칭(JOIN)합니다.
# 지역별 전체 사고 수에 전국 하원시간 사고 비율을 곱해 '위험도 지수'를 계산하는 고급 기법을 사용했습니다!
query3 = """
    WITH AfternoonStats AS (
        -- 1. 2024년 평일 하원 시간(16~18시) 전체 사고 수 합계
        SELECT 
            년도,
            SUM("월요일 사고 수" + "화요일 사고 수" + "수요일 사고 수" + "목요일 사고 수" + "금요일 사고 수") AS 전체_하원시간_사고수
        FROM "요일별, 시간대별 교통사고 통계 최최종"
        WHERE 시간 IN ('16시', '17시', '18시') AND 년도 = 2024
        GROUP BY 년도
    ),
    RegionStats AS (
        -- 2. 시군구별 통계에서 2024년 사고 수 추출 (JOIN을 위해 년도 2024 생성)
        SELECT 
            시군구, 
            "2024" AS 지역별_사고수,
            2024 AS 년도
        FROM "시군구별 교통사고 통계"
    )
    -- 3. '년도'를 기준으로 JOIN 하여 지역별 위험도 지수 산출
    SELECT 
        r.시군구,
        r.지역별_사고수,
        -- 지역 사고수에 비례하여 하원 시간대 위험도 추정
        (r.지역별_사고수 * a.전체_하원시간_사고수) AS 하원시간_위험도_지수 
    FROM RegionStats r
    JOIN AfternoonStats a ON r.년도 = a.년도
    ORDER BY 하원시간_위험도_지수 DESC
    LIMIT 10
"""
