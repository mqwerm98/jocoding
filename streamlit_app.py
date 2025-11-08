import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="AI Bitcoin Trading Dashboard", layout="wide")

st.title("💹 AI Bitcoin Trading Dashboard")
st.markdown("자동매매 내역, 공포·탐욕지수, 잔고, 수익률을 시각화합니다.")

csv_file = "trade_history.csv"

# --- CSV 파일 확인 ---
if not os.path.exists(csv_file):
    st.warning("⚠️ 아직 거래 내역 CSV 파일이 없습니다. 트레이딩 코드 실행 후 다시 확인해주세요.")
    st.stop()

# --- CSV 불러오기 ---
df = pd.read_csv(csv_file)

# --- datetime 처리 ---
if "datetime" not in df.columns:
    st.error("❌ CSV에 'datetime' 컬럼이 없습니다. 파일 구조를 확인해주세요.")
    st.stop()

df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

# --- 결측치 제거 ---
df = df.dropna(subset=["datetime", "krw_balance", "btc_balance"], how="any")

# --- 총 자산 및 수익률 계산 ---
# CSV에 이미 total_asset 컬럼이 있으면 사용, 없으면 계산
if "total_asset" not in df.columns:
    df["total_asset"] = df["krw_balance"]

initial_asset = df["total_asset"].iloc[0]
df["profit_rate"] = (df["total_asset"] / initial_asset - 1) * 100

# --- 기본 데이터 미리보기 ---
st.subheader("📊 Raw Data")
st.dataframe(df.tail(20))

# --- 공포탐욕지수 그래프 ---
if "fear_and_greed" in df.columns:
    st.subheader("😨 Fear and Greed Index Trend")
    fig_fng = px.line(df, x="datetime", y="fear_and_greed", markers=True,
                      title="Fear & Greed Index Over Time")
    st.plotly_chart(fig_fng, use_container_width=True)

# --- 잔고 그래프 (KRW, BTC) ---
col1, col2 = st.columns(2)

with col1:
    if "krw_balance" in df.columns:
        st.subheader("💰 KRW Balance")
        fig_krw = px.line(df, x="datetime", y="krw_balance", markers=True,
                          title="KRW Balance Over Time (₩)")
        st.plotly_chart(fig_krw, use_container_width=True)

with col2:
    if "btc_balance" in df.columns:
        st.subheader("🪙 BTC Balance")
        fig_btc = px.line(df, x="datetime", y="btc_balance", markers=True,
                          title="BTC Balance Over Time (BTC)")
        st.plotly_chart(fig_btc, use_container_width=True)

# --- 💹 수익률 그래프 ---
st.subheader("📈 Profit Rate (%) Over Time")
fig_profit = px.line(df, x="datetime", y="profit_rate", markers=True,
                     title="Cumulative Profit Rate (%)",
                     color_discrete_sequence=["green" if df["profit_rate"].iloc[-1] >= 0 else "red"])
st.plotly_chart(fig_profit, use_container_width=True)

# --- 수익 요약 ---
latest_profit = df["profit_rate"].iloc[-1]
st.metric("현재 누적 수익률", f"{latest_profit:.2f} %",
          delta=f"{latest_profit - df['profit_rate'].iloc[-2]:.2f} %" if len(df) > 1 else None)

# --- AI 판단 통계 ---
if "decision" in df.columns:
    st.subheader("🤖 AI Decision Statistics")
    decision_counts = df["decision"].value_counts().reset_index()
    decision_counts.columns = ["Decision", "Count"]
    fig_decision = px.pie(decision_counts, names="Decision", values="Count",
                          title="Distribution of AI Trading Decisions",
                          color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_decision, use_container_width=True)

# --- 거래 로그 ---
st.subheader("🧾 Trade Execution Log")
for _, row in df.tail(10).iterrows():
    dt = row["datetime"]
    decision = row.get("decision", "UNKNOWN").upper()
    with st.expander(f"{dt} | {decision}"):
        st.write(f"**Reason:** {row.get('reason', 'No reason provided')}")
        st.write(f"**Fear & Greed Index:** {row.get('fear_and_greed', 'N/A')}")
        st.write(f"**KRW Balance:** ₩{row.get('krw_balance', 0):,.0f}")
        st.write(f"**BTC Balance:** {row.get('btc_balance', 0):.6f} BTC")
        st.write(f"**Action Result:** {row.get('action_result', 'N/A')}")

st.markdown("---")
st.caption("ⓒ 2025 JoCoding AI Trading Dashboard — Powered by Streamlit")
