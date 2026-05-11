import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 페이지 및 디자인 설정 (글래스모피즘)
# ==========================================
st.set_page_config(page_title="공공데이터 안전 대시보드", layout="wide")

# 글래스모피즘 CSS 스타일 적용
glassmorphism_css = """
<style>
    /* 배경 설정 (원하는 배경색이나 그라데이션으로 변경 가능) */
    .stApp {
        background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
    }
    
    /* 글래스모피즘 카드 UI 적용 */
    div[data-testid="stVerticalBlock"] > div {
        background: rgba(255, 255, 255, 0.25) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2) !important;
        margin-bottom: 1rem !important;
    }
    
    /* 텍스트 색상 조정 */
    h1, h2, h3, p, li {
        color: #2c3e50 !important;
    }
</style>
"""
st.markdown(glassmorphism_css, unsafe_allow_html=True)

# ==========================================
# 2. 데이터베이스 연결 및 에러 처리
# ==========================================
# 요청사항: safety.db 파일이 없으면 친절한 에러 메시지 띄우기
# (설명에는 mydbdb.db로 되어 있으므로 두 가지 경우 모두 체크하도록 유연하게 작성했습니다)
db_file = "mydbdb.db"
if not os.path.exists(db_file) and not os.path.exists("safety.db"):
    st.error("데이터베이스 파일을 찾을 수 없습니다. 😢 (mydbdb.db 또는 safety.db 파일을 같은 폴더에 넣어주세요!)")
    st.stop() # 프로그램 실행 중단

# ==========================================
# 3. 데이터 로드 함수 (모듈화)
# ==========================================
@st.cache_data # 데이터 캐싱을 통해 앱 속도를 높여줍니다!
def load_data(query):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.title("🛡️ 우리 동네 어린이 안전 대시보드")
st.markdown("시군구별 어린이집 데이터와 교통사고 통계를 분석한 대시보드입니다.")

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
fig1.add_trace(go.Bar(x=df1['시군구'], y=df1['통학차량_운영_어린이집수'], name="통학차량 운영 수", marker_color='rgba(52, 152, 219, 0.7)'), secondary_y=False)
fig1.add_trace(go.Scatter(x=df1['시군구'], y=df1['2024년_사고수'], name="2024년 사고 수", mode='lines+markers', line=dict(color='rgba(231, 76, 60, 1)', width=3)), secondary_y=True)
fig1.update_layout(title_text="시군구별 통학차량 어린이집 수 vs 교통사고 수 (2024)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig1, use_container_width=True)

# ② 사용한 SQL
with st.expander("📝 사용한 SQL 쿼리 보기"):
    st.code(query1, language="sql")

# ③ 분석 인사이트
st.info("""
**💡 분석 인사이트**
* 통학차량을 많이 운영하는 지역일수록 교통사고 발생 건수와 비례하는지, 혹은 반비례하는지 패턴을 파악할 수 있습니다.
* 통학차량은 많으나 사고 수가 적은 자치구는 교통안전 관리가 우수하게 이루어지고 있을 확률이 높습니다.
""")

# ==========================================
# 5. 차트 2: 어린이집 현원율과 사고 위험도
# ==========================================
st.header("2. 어린이집 정원 대비 현원율과 사고 위험도")

query2 = """
    SELECT 
        a.시군구,
        -- 현원율 계산 (정원이 0인 경우 나누기 에러 방지)
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
fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig2, use_container_width=True)

# ② 사용한 SQL
with st.expander("📝 사용한 SQL 쿼리 보기"):
    st.code(query2, language="sql")

# ③ 분석 인사이트
st.info("""
**💡 분석 인사이트**
* 현원율(보육 밀집도)이 높은 지역이 아이들의 통행량이 많아져 사고 건수가 높은지 상관관계를 점검할 수 있습니다.
* 우상단에 위치한 자치구(현원율도 높고 사고도 많은 곳)는 우선적인 어린이 보호구역 점검 및 예산 투입이 필요합니다.
""")

# ==========================================
# 6. 차트 3: 평일 하원 시간대 사고 비중 분석
# ==========================================
st.header("3. 평일 하원 시간대(16시~18시) 사고 취약 상위 10개 지역")

# 멘토의 메모: 시간대별 통계 테이블에 '시군구' 컬럼이 있다고 가정한 쿼리입니다.
query3 = """
    SELECT 
        a.시군구,
        SUM(c."월요일 사고 수" + c."화요일 사고 수" + c."수요일 사고 수" + c."목요일 사고 수" + c."금요일 사고 수") AS 평일_하원시간_사고수
    FROM "시군구별 교통사고 통계" a
    JOIN "요일별, 시간대별 교통사고 통계 최최종" c ON a.시군구 = c.시군구
    WHERE c.시간 IN ('16시', '17시', '18시')
    GROUP BY a.시군구
    ORDER BY 평일_하원시간_사고수 DESC
    LIMIT 10
"""
df3 = load_data(query3)

# ① 시각화 (가로 막대 차트)
# 상위 값이 위에 오도록 y축 설정 변경 (ascending=True 로 뒤집어줌)
fig3 = px.bar(df3.sort_values('평일_하원시간_사고수', ascending=True), 
              x="평일_하원시간_사고수", y="시군구", orientation='h', 
              title="평일 16~18시 사고 발생 상위 10개 지역",
              color="평일_하원시간_사고수", color_continuous_scale="Reds")
fig3.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig3, use_container_width=True)

# ② 사용한 SQL
with st.expander("📝 사용한 SQL 쿼리 보기"):
    st.code(query3, language="sql")

# ③ 분석 인사이트
st.info("""
**💡 분석 인사이트**
* 아이들이 가장 많이 하원하는 16시~18시 사이에 유독 평일 사고가 집중되는 상위 10개 지역을 도출했습니다.
* 해당 지역들은 하원 시간에 맞춰 하차 구역 불법주정차 단속을 강화하거나 녹색어머니회 활동을 집중할 필요가 있습니다.
""")