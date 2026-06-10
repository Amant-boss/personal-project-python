import streamlit as st
import requests
import pandas as pd
import plotly.express as px

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Sports Stats Analyzer", page_icon="", layout="wide")
st.title("Sports Statistics Analyzer")
st.caption("Analyzing historical rosters, logging live matches, and forecasting performance trends.")

tab_data, tab_stats, tab_compare, tab_predict, tab_raw_analytics = st.tabs([
    "Data Management",
    "Advanced Statistics",
    "Compare Players",
    "Performance Trends",
    "Raw Analytics"
])

player_list = []
df_existing = pd.DataFrame()

with tab_data:
    st.header("Current Roster & Database Status")
    try:
        response = requests.get(f"{BACKEND_URL}/players")
        if response.status_code == 200:
            player_list = response.json()
            if player_list:
                df_existing = pd.DataFrame(player_list)
                st.success(f"Connected to Database: {len(df_existing)} players loaded from database.")
                st.dataframe(df_existing, use_container_width=True, hide_index=True)
            else:
                st.info("The database file exists but it is currently empty.")
        else:
            st.warning("⚠️ No existing data found in the backend database yet.")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to FastAPI backend. Make sure your Uvicorn server is running (api.py).")

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
            submit_manual = st.form_submit_button("Append to Database")

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

        with st.expander("Edit & Modify Existing Records"):
            if player_list:
                options = [f"{p['first_name']} {p['last_name']}" for p in player_list]
                selected_player_name = st.selectbox("Select Player to Edit", options, key="edit_select")

                selected_idx = options.index(selected_player_name)
                p_current = player_list[selected_idx]

                with st.form("edit_entry_form"):
                    edit_f = st.text_input("First Name", value=p_current["first_name"])
                    edit_l = st.text_input("Last Name", value=p_current["last_name"])
                    edit_team = st.text_input("Team", value=p_current["team"])
                    edit_nat = st.text_input("Nationality", value=p_current.get("nationality", ""))
                    edit_pos = st.selectbox("Position", ["Forward", "Midfielder", "Defender"],
                                            index=["Forward", "Midfielder", "Defender"].index(p_current["position"]) if
                                            p_current["position"] in ["Forward", "Midfielder", "Defender"] else 0)

                    em1, em2, em3 = st.columns(3)
                    with em1:
                        edit_matches = st.number_input("Matches Played", min_value=0, step=1,
                                                       value=int(p_current["matches_played"]))
                    with em2:
                        edit_goals = st.number_input("Goals", min_value=0, step=1, value=int(p_current["goals"]))
                    with em3:
                        edit_assists = st.number_input("Assists", min_value=0, step=1, value=int(p_current["assists"]))

                    edit_minutes = st.number_input("Minutes Played", min_value=0, step=1,
                                                   value=int(p_current["minutes_played"]))

                    submit_edit = st.form_submit_button("Save Changes to Database")
                    if submit_edit:
                        edit_payload = {
                            "first_name": edit_f,
                            "last_name": edit_l,
                            "team": edit_team,
                            "nationality": edit_nat,
                            "position": edit_pos,
                            "matches_played": int(edit_matches),
                            "goals": int(edit_goals),
                            "assists": int(edit_assists),
                            "minutes_played": int(edit_minutes)
                        }
                        params = {"old_first": p_current["first_name"], "old_last": p_current["last_name"]}
                        res = requests.put(f"{BACKEND_URL}/player/update", params=params, json=edit_payload)
                        if res.status_code == 200:
                            st.success(f"Successfully updated record for {edit_f} {edit_l}!")
                            st.rerun()
                        else:
                            st.error(f"Error updating record: {res.text}")
            else:
                st.info("No data available to edit.")

        with st.expander("Delete Player Record"):
            if player_list:
                del_options = [f"{p['first_name']} {p['last_name']}" for p in player_list]
                target_del = st.selectbox("Select Player to Permanently Delete", del_options, key="del_select")

                if st.button("Confirm Delete", key="delete_confirm_btn", type="primary"):
                    del_idx = del_options.index(target_del)
                    p_to_del = player_list[del_idx]

                    del_params = {"first_name": p_to_del["first_name"], "last_name": p_to_del["last_name"]}
                    res = requests.delete(f"{BACKEND_URL}/player/delete", params=del_params)
                    if res.status_code == 200:
                        st.success(f"Successfully deleted {target_del} from database!")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete record: {res.text}")
            else:
                st.info("No database elements to delete.")

        with st.expander("Overwrite Current Database with a new CSV"):
            uploaded_file = st.file_uploader("Upload replacement sports data CSV", type=["csv"])
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
    st.header("Individual Player Advanced Metrics")
    search_player = st.text_input("Enter Player Last Name to fetch metrics:", key="search_single")

    if search_player:
        if st.button("Calculate Stats", key="calc_stats_btn"):
            try:
                response = requests.get(f"{BACKEND_URL}/player/{search_player}/stats")
                if response.status_code == 200:
                    data = response.json()

                    # Core KPI Metrics
                    col1, col2, col3 = st.columns(3)
                    col1.metric(label="Goal Conversion per 90 Min", value=data.get("goals_per_90", "N/A"))
                    col2.metric(label="Total Goal Involvements", value=data.get("goal_involvements", "N/A"))
                    col3.metric(label="League Efficiency Rank", value=f"#{data.get('rank', 'N/A')}")

                    st.write("---")

                    # Advanced Visualizations Split
                    stat_plot_col1, stat_plot_col2 = st.columns(2)

                    with stat_plot_col1:
                        # Individual Contribution Profile
                        mix_df = pd.DataFrame({
                            "Metric": ["Goals", "Assists"],
                            "Value": [data.get("goals", 0), data.get("assists", 0)]
                        })
                        fig_mix = px.pie(mix_df, names="Metric", values="Value", hole=0.4,
                                         title=f"Attacking Contribution Profile: {data.get('first_name')} {data.get('last_name')}",
                                         color_discrete_sequence=["#FF4B4B", "#0068C9"])
                        st.plotly_chart(fig_mix, use_container_width=True)

                    with stat_plot_col2:
                        # Baseline Comparison Matrix against complete Roster
                        if not df_existing.empty:
                            avg_goals = round(df_existing["goals"].mean(), 2)
                            avg_assists = round(df_existing["assists"].mean(), 2)
                            avg_matches = round(df_existing["matches_played"].mean(), 2)

                            bench_df = pd.DataFrame({
                                "Metric": ["Matches", "Goals", "Assists"],
                                "This Player": [data.get("matches_played", 0), data.get("goals", 0),
                                                data.get("assists", 0)],
                                "League Avg": [avg_goals, avg_assists, avg_matches]
                            }).melt(id_vars="Metric", var_name="Scope", value_name="Total")

                            fig_bench = px.bar(bench_df, x="Metric", y="Total", color="Scope", barmode="group",
                                               title="Output Velocity vs. Database Baselines",
                                               color_discrete_sequence=["#29B5E8", "#FFABAB"])
                            st.plotly_chart(fig_bench, use_container_width=True)

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

                    # Chart 1: Grouped Clustered Performance Bar
                    st.subheader("Performance Volumetric Breakdown")
                    fig = px.bar(df, x="metrics", y=[p1_name, p2_name], barmode="group",
                                 title=f"Head-to-Head: {p1_name} vs {p2_name}",
                                 color_discrete_sequence=["#7A1FA2", "#0097A7"])
                    st.plotly_chart(fig, use_container_width=True)

                    st.write("---")
                    comp_graph_col1, comp_graph_col2 = st.columns(2)

                    with comp_graph_col1:
                        # Chart 2: Polar Radar Chart Structure for Attribute Footprints
                        radar_filter = df[df["metrics"] != "Goals per 90"]
                        df_radar = radar_filter.melt(id_vars="metrics", var_name="Player", value_name="Volume")

                        fig_radar = px.line_polar(df_radar, r="Volume", theta="metrics", color="Player",
                                                  line_close=True,
                                                  title="Stat Distribution Coverage Area",
                                                  color_discrete_sequence=["#7A1FA2", "#0097A7"])
                        # FIXED: Corrected from "adjacent" to "toself"
                        fig_radar.update_traces(fill="toself")
                        st.plotly_chart(fig_radar, use_container_width=True)

                    with comp_graph_col2:
                        # Chart 3: Absolute Dominance Percentage Split
                        p1_g = df[df["metrics"] == "Goals"][p1_name].values[0]
                        p2_g = df[df["metrics"] == "Goals"][p2_name].values[0]

                        if (p1_g + p2_g) > 0:
                            share_df = pd.DataFrame({
                                "Player": [p1_name, p2_name],
                                "Total Goals": [p1_g, p2_g]
                            })
                            fig_share = px.pie(share_df, names="Player", values="Total Goals", hole=0.5,
                                               title="Total Combined Goal Share Comparison",
                                               color_discrete_sequence=["#7A1FA2", "#0097A7"])
                            st.plotly_chart(fig_share, use_container_width=True)
                        else:
                            st.info(
                                "Both target players currently maintain 0 goals, skipping share distribution mapping.")
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

with tab_raw_analytics:
    st.header("Aggregated Roster Analytics")
    st.caption("Real-time automated visualizations mapping entire global dataset matrices.")

    if not df_existing.empty:
        df_existing["full_name"] = df_existing["first_name"] + " " + df_existing["last_name"]

        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            fig_pie = px.pie(df_existing, names="full_name", values="goals", title="Squad Goal Share Distribution",
                             hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)
        with row1_col2:
            df_sorted = df_existing.sort_values(by="goals", ascending=False)
            fig_bar = px.bar(df_sorted, x="full_name", y=["goals", "assists"], barmode="group",
                             title="Goal vs Assist Production Rankings")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.write("---")

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            df_pos = df_existing.groupby("position").agg({"goals": "sum", "assists": "sum"}).reset_index()
            fig_pos = px.bar(df_pos, x="position", y=["goals", "assists"], barmode="group",
                             title="Attacking Volume Breakdown by Position Group")
            st.plotly_chart(fig_pos, use_container_width=True)
        with row2_col2:
            df_team = df_existing.groupby("team")["goals"].sum().reset_index().sort_values(by="goals", ascending=False)
            fig_team = px.bar(df_team, x="team", y="goals", title="Total Club Goals League Standings", color="team")
            st.plotly_chart(fig_team, use_container_width=True)

        st.write("---")

        row3_col1, row3_col2 = st.columns(2)
        with row3_col1:
            fig_scatter = px.scatter(df_existing, x="minutes_played", y="goals", color="position",
                                     size="matches_played", hover_name="full_name",
                                     title="Work Rate vs Output: Minutes Logged vs Goals Converted")
            st.plotly_chart(fig_scatter, use_container_width=True)
        with row3_col2:
            fig_nat = px.histogram(df_existing, x="nationality",
                                   title="Roster Cultural Demographic Composition Matrix", color="position")
            st.plotly_chart(fig_nat, use_container_width=True)
    else:
        st.info("Add records or check backend server data inside database files to visualize metrics.")