import streamlit as st
import requests
import pandas as pd
import plotly.express as px

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Sports Stats Analyzer", page_icon="🏆", layout="wide")
st.title("🏆 Sports Statistics Analyzer")
st.caption("Analyzing historical rosters, logging live matches, and forecasting performance trends.")

tab_data, tab_stats, tab_compare, tab_predict = st.tabs([
    "📁 Data Management",
    "📊 Advanced Statistics",
    "⚔️ Compare Players",
    "📈 Performance Trends"
])

with tab_data:
    st.header("Current Roster & Database Status")
    try:
        response = requests.get(f"{BACKEND_URL}/players")
        if response.status_code == 200:
            player_list = response.json()
            if player_list:
                df_existing = pd.DataFrame(player_list)
                st.success(f"✅ Connected to Database: {len(df_existing)} players loaded from 'data/sports_data.csv'")
                st.dataframe(df_existing, use_container_width=True, hide_index=True)
            else:
                st.info("The database file exists but it is currently empty.")
        else:
            st.warning("⚠️ No existing sports_data.csv found in the backend 'data' folder yet.")
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to FastAPI backend. Make sure your Uvicorn server is running (api.py).")

    st.write("---")
    col_manual, col_csv = st.columns(2)

    with col_manual:
        st.subheader("Add New Player / Log Live Match Data")
        with st.form("manual_entry_form", clear_on_submit=True):
            f_name = st.text_input("First Name")
            l_name = st.text_input("Last Name")
            team = st.text_input("Team")
            nat = st.text_input("Nationality")
            pos = st.selectbox("Position", ["Forward", "Midfielder", "Defender"])

            m1, m2, m3 = st.columns(3)
            with m1:
                matches = st.number_input("Matches Played", min_value=0, step=1)
            with m2:
                goals = st.number_input("Goals", min_value=0, step=1)
            with m3:
                assists = st.number_input("Assists", min_value=0, step=1)

            minutes = st.number_input("Minutes Played", min_value=0, step=1)
            submit_manual = st.form_submit_button("Append to Local CSV")

            if submit_manual:
                if not f_name or not l_name or not team:
                    st.warning("Please fill out at least First Name, Last Name, and Team.")
                else:
                    payload = {
                        "first_name": f_name,
                        "last_name": l_name,
                        "team": team,
                        "nationality": nat,
                        "position": pos,
                        "matches_played": int(matches),
                        "goals": int(goals),
                        "assists": int(assists),
                        "minutes_played": int(minutes)
                    }
                    try:
                        res = requests.post(f"{BACKEND_URL}/player/add", json=payload)
                        if res.status_code == 200:
                            st.success(f"Successfully added {f_name} {l_name}!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add data: {res.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to FastAPI backend.")

    with col_csv:
        st.subheader("Advanced Settings")
        with st.expander("Overwrite Current Database with a new CSV"):
            uploaded_file = st.file_uploader("Upload replacement sports_data.csv", type=["csv"])
            if uploaded_file is not None:
                if st.button("Danger: Overwrite Existing Data", key="upload_csv_btn"):
                    with st.spinner("Replacing file on backend..."):
                        try:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                            res = requests.post(f"{BACKEND_URL}/upload", files=files)
                            if res.status_code == 200:
                                st.success("Database overwritten successfully!")
                                st.rerun()
                            else:
                                st.error(f"Backend Error: {res.text}")
                        except requests.exceptions.ConnectionError:
                            st.error("Backend unreachable.")

with tab_stats:
    st.header("Player & Team Advanced Metrics")
    search_player = st.text_input("Enter Player Last Name to fetch metrics:", key="search_single")

    if search_player:
        if st.button("Calculate Stats", key="calc_stats_btn"):
            try:
                response = requests.get(f"{BACKEND_URL}/player/{search_player}/stats")
                if response.status_code == 200:
                    data = response.json()
                    col1, col2, col3 = st.columns(3)
                    col1.metric(label="Goal Conversion per 90 Min", value=data.get("goals_per_90", "N/A"))
                    col2.metric(label="Total Goal Involvements", value=data.get("goal_involvements", "N/A"))
                    col3.metric(label="League Efficiency Rank", value=f"#{data.get('rank', 'N/A')}")
                    st.subheader("Full Metric Breakdown")
                    st.json(data)
                else:
                    st.warning("Player not found in backend database.")
            except requests.exceptions.ConnectionError:
                st.error("Backend unreachable.")

with tab_compare:
    st.header("Player vs Player Comparison")
    cp1, cp2 = st.columns(2)
    with cp1:
        p1_name = st.text_input("First Player (Last Name):", key="compare_p1")
    with cp2:
        p2_name = st.text_input("Second Player (Last Name):", key="compare_p2")

    if p1_name and p2_name:
        if st.button("Run Comparison Graph", key="compare_btn"):
            try:
                response = requests.post(f"{BACKEND_URL}/compare", json={"p1": p1_name, "p2": p2_name})
                if response.status_code == 200:
                    comp_data = response.json()
                    df = pd.DataFrame(comp_data)
                    fig = px.bar(df, x="metrics", y=[p1_name, p2_name], barmode="group",
                                 title=f"Head-to-Head: {p1_name} vs {p2_name}")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Backend failed to process the comparison payload.")
            except requests.exceptions.ConnectionError:
                st.error("Backend unreachable.")

with tab_predict:
    st.header("Future Performance Forecasting")
    target_player = st.text_input("Enter Player Last Name for Trend Analysis:", key="predict_target")

    if target_player:
        if st.button("Generate Trend Line", key="predict_btn"):
            try:
                response = requests.get(f"{BACKEND_URL}/player/{target_player}/predict")
                if response.status_code == 200:
                    trend_data = response.json()
                    df_trend = pd.DataFrame(trend_data)
                    fig_trend = px.line(df_trend, x="games", y=["historical_goals", "predicted_trend"],
                                        labels={"value": "Goals / Impact", "variable": "Data Type"},
                                        title=f"Performance Trajectory for {target_player}")
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.error("Could not compute trend line for this player.")
            except requests.exceptions.ConnectionError:
                st.error("Backend unreachable.")