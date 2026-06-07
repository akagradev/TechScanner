from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from companies import COMPANIES

DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "mentions.csv"


def load_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        pd.DataFrame(columns=["date", "company", "count"]).to_csv(CSV_PATH, index=False)
        return pd.DataFrame(columns=["date", "company", "count"])

    df = pd.read_csv(CSV_PATH)
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    return df


st.set_page_config(page_title="Bloomberg Tech AI Signal Tracker", layout="wide")
st.title("Bloomberg Tech AI Signal Tracker")

df = load_data()

st.header("Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Companies Tracked", len(COMPANIES))
col2.metric("Historical Records", len(df))
latest_date = df["date"].max() if not df.empty else None
col3.metric("Latest Date", latest_date.strftime("%Y-%m-%d") if latest_date is not None else "N/A")

st.header("Today's Rankings")

if df.empty or latest_date is None:
    st.info("No data yet. Run the scraper to populate mentions.")
else:
    latest_df = df[df["date"] == latest_date].copy()
    rankings = (
        latest_df[["company", "count"]]
        .rename(columns={"company": "Company", "count": "Mentions"})
        .sort_values("Mentions", ascending=False)
        .reset_index(drop=True)
    )
    st.dataframe(rankings, use_container_width=True, hide_index=True)

st.header("Historical Trend")

if df.empty:
    st.info("No historical data available yet.")
else:
    company = st.selectbox("Select Company", sorted(df["company"].unique()))
    company_df = df[df["company"] == company].sort_values("date")

    fig = px.line(
        company_df,
        x="date",
        y="count",
        markers=True,
        labels={"date": "Date", "count": "Mentions"},
        title=f"{company} Mentions Over Time",
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("Biggest Movers")

if df.empty or latest_date is None:
    st.info("Need at least one day of data to show movers.")
else:
    unique_dates = sorted(df["date"].unique())
    if len(unique_dates) < 2:
        st.info("Need at least two days of data to calculate movers.")
    else:
        today_df = df[df["date"] == unique_dates[-1]].set_index("company")["count"]
        yesterday_df = df[df["date"] == unique_dates[-2]].set_index("company")["count"]

        movers = []
        for company in COMPANIES:
            today_count = int(today_df.get(company, 0))
            yesterday_count = int(yesterday_df.get(company, 0))
            pct_change = (today_count - yesterday_count) / max(yesterday_count, 1) * 100
            movers.append(
                {
                    "Company": company,
                    "Yesterday": yesterday_count,
                    "Today": today_count,
                    "Change %": round(pct_change, 1),
                }
            )

        movers_df = (
            pd.DataFrame(movers)
            .sort_values("Change %", ascending=False)
            .reset_index(drop=True)
        )
        st.dataframe(movers_df, use_container_width=True, hide_index=True)
