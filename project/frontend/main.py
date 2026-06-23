import streamlit as st
import requests
import pandas as pd
import plotly.express as px

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Sports Stats Analyzer", page_icon="🏀", layout="wide")
st.title("Sports Statistics Analyzer")
st.caption("Analyzing historical rosters, logging live matches, and forecasting performance trends.")

# Global Sport Selector Sidebar Filter
st.sidebar.header("Navigation Settings")
selected_sport = st.sidebar.selectbox("Choose Sport Profile Mode", ["Footballer", "Basketballer"])

tab_data, tab_stats, tab_compare, tab_predict, tab_raw_analytics = st.tabs([
    "Data Management",
    "Advanced Statistics",
    "Compare Players",
    "Performance Trends",
    "Raw Analytics"
])

player_list = []
df_existing = pd.DataFrame()
df_filtered = pd.DataFrame()

# Global Data Pulling & Safety checks
try:
    response = requests.get(f"{BACKEND_URL}/players")
    if response.status_code == 200:
        player_list = response.json()
        if player_list:
            df_existing = pd.DataFrame(player_list)
            # Safe parsing for newly introduced 'sport' schemas
            if "sport" in df_existing.columns:
                df_filtered = df_existing[df_existing["sport"] == selected_sport].reset_index(drop=True)
            else:
                df_filtered = pd.DataFrame()  # Avoids failure logs if DB is unmigrated
except requests.exceptions.ConnectionError:
    pass

with tab_data:
    st.header(f"Current {selected_sport} Roster Status")

    if not df_filtered.empty:
        st.success(f"Connected to Database: {len(df_filtered)} loaded for {selected_sport} configuration.")
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    elif not df_existing.empty and df_filtered.empty:
        st.info(f"The database has entries, but no records exist yet for the category: '{selected_sport}'.")
    else:
        st.info("The database file is completely empty or server is offline.")

    st.write("---")
    col_manual, col_csv = st.columns(2)

    with col_manual:
        st.subheader(f"Add New {selected_sport} Data")
        with st.form("manual_entry_form", clear_on_submit=True):
            f_name = st.text_input("First Name")
            l_name = st.text_input("Last Name")
            team = st.text_input("Team")
            nat = st.text_input("Nationality")

            # Position layout adapts dynamically to provide clean visual categorization
            pos_options = ["Forward", "Midfielder", "Defender"] if selected_sport == "Footballer" else ["Guard",
                                                                                                        "Forward",
                                                                                                        "Center"]
            pos = st.selectbox("Position", pos_options)

            m1, m2, m3 = st.columns(3)
            with m1:
                matches = st.number_input("Matches Played", min_value=0, step=1)
            with m2:
                # Value label tracking adaptivity
                score_label = "Goals" if selected_sport == "Footballer" else "Points Logged"
                goals = st.number_input(score_label, min_value=0, step=1)
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
                        "sport": selected_sport,
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
            if not df_filtered.empty:
                filtered_list = df_filtered.to_dict(orient="records")
                options = [f"{p['first_name']} {p['last_name']}" for p in filtered_list]
                selected_player_name = st.selectbox("Select Player to Edit", options, key="edit_select")

                selected_idx = options.index(selected_player_name)
                p_current = filtered_list[selected_idx]

                with st.form("edit_entry_form"):
                    edit_f = st.text_input("First Name", value=p_current["first_name"])
                    edit_l = st.text_input("Last Name", value=p_current["last_name"])
                    edit_team = st.text_input("Team", value=p_current["team"])
                    edit_nat = st.text_input("Nationality", value=p_current.get("nationality", ""))

                    pos_opts = ["Forward", "Midfielder", "Defender"] if selected_sport == "Footballer" else ["Guard",
                                                                                                             "Forward",
                                                                                                             "Center"]
                    idx_pos = pos_opts.index(p_current["position"]) if p_current["position"] in pos_opts else 0
                    edit_pos = st.selectbox("Position", pos_opts, index=idx_pos)

                    em1, em2, em3 = st.columns(3)
                    with em1:
                        edit_matches = st.number_input("Matches Played", min_value=0, step=1,
                                                       value=int(p_current["matches_played"]))
                    with em2:
                        edit_goals = st.number_input("Scoring Stats Total", min_value=0, step=1,
                                                     value=int(p_current["goals"]))
                    with em3:
                        edit_assists = st.number_input("Assists", min_value=0, step=1, value=int(p_current["assists"]))

                    edit_minutes = st.number_input("Minutes Played", min_value=0, step=1,
                                                   value=int(p_current["minutes_played"]))

                    submit_edit = st.form_submit_button("Save Changes to Database")
                    if submit_edit:
                        edit_payload = {
                            "first_name": edit_f,
                            "last_name": edit_l,
                            "sport": selected_sport,
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
                st.info(f"No {selected_sport} available to edit.")

        with st.expander("Delete Player Record"):
            if not df_filtered.empty:
                filtered_list = df_filtered.to_dict(orient="records")
                del_options = [f"{p['first_name']} {p['last_name']}" for p in filtered_list]
                target_del = st.selectbox("Select Player to Permanently Delete", del_options, key="del_select")

                if st.button("Confirm Delete", key="delete_confirm_btn", type="primary"):
                    del_idx = del_options.index(target_del)
                    p_to_del = filtered_list[del_idx]

                    del_params = {"first_name": p_to_del["first_name"], "last_name": p_to_del["last_name"]}
                    res = requests.delete(f"{BACKEND_URL}/player/delete", params=del_params)
                    if res.status_code == 200:
                        st.success(f"Successfully deleted {target_del} from database!")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete record: {res.text}")
            else:
                st.info("No interactive sports elements to delete.")

        with st.expander("Overwrite Current Database with a new CSV"):
            st.caption(
                "Note: To support multiple branches, ensure your loaded file contains a 'sport' field column populated with 'Footballer' or 'Basketballer'.")
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
    st.header(f"Individual {selected_sport} Advanced Metrics")
    search_player = st.text_input("Enter Player Last Name to fetch metrics:", key="search_single")

    if search_player:
        if st.button("Calculate Stats", key="calc_stats_btn"):
            try:
                response = requests.get(f"{BACKEND_URL}/player/{search_player}/stats")
                if response.status_code == 200:
                    data = response.json()

                    if data.get("sport") != selected_sport:
                        st.warning(
                            f"Found record for '{search_player}', but they belong to a different profile layer ({data.get('sport')}). Switch your filter to view details.")
                    else:
                        # Core KPI Metrics
                        eff_label = "Production rate per 90 Min" if selected_sport == "Footballer" else "Points efficiency per 90 Min"
                        score_term = "Total Goal Involvements" if selected_sport == "Footballer" else "Point Involvements"

                        col1, col2, col3 = st.columns(3)
                        col1.metric(label=eff_label, value=data.get("goals_per_90", "N/A"))
                        col2.metric(label=score_term, value=data.get("goal_involvements", "N/A"))
                        col3.metric(label="Profile Efficiency Rank", value=f"#{data.get('rank', 'N/A')}")

                        st.write("---")

                        stat_plot_col1, stat_plot_col2 = st.columns(2)

                        with stat_plot_col1:
                            mix_df = pd.DataFrame({
                                "Metric": ["Scoring Metric", "Assists"],
                                "Value": [data.get("goals", 0), data.get("assists", 0)]
                            })
                            fig_mix = px.pie(mix_df, names="Metric", values="Value", hole=0.4,
                                             title=f"Output Breakdown Matrix: {data.get('first_name')} {data.get('last_name')}",
                                             color_discrete_sequence=["#FF4B4B", "#0068C9"])
                            st.plotly_chart(fig_mix, use_container_width=True)

                        with stat_plot_col2:
                            if not df_filtered.empty:
                                avg_goals = round(df_filtered["goals"].mean(), 2)
                                avg_assists = round(df_filtered["assists"].mean(), 2)
                                avg_matches = round(df_filtered["matches_played"].mean(), 2)

                                bench_df = pd.DataFrame({
                                    "Metric": ["Matches", "Scoring Output", "Assists"],
                                    "This Player": [data.get("matches_played", 0), data.get("goals", 0),
                                                    data.get("assists", 0)],
                                    "Profile Avg": [avg_goals, avg_assists, avg_matches]
                                }).melt(id_vars="Metric", var_name="Scope", value_name="Total")

                                fig_bench = px.bar(bench_df, x="Metric", y="Total", color="Scope", barmode="group",
                                                   title=f"Output Velocity vs {selected_sport} Baselines",
                                                   color_discrete_sequence=["#29B5E8", "#FFABAB"])
                                st.plotly_chart(fig_bench, use_container_width=True)

                        st.subheader("Full Metric Breakdown")
                        st.json(data)
                else:
                    st.warning("Player not found in backend database.")
            except requests.exceptions.ConnectionError:
                st.error("Backend unreachable.")

with tab_compare:
    st.header(f"Head-to-Head {selected_sport} Evaluation")
    cp1, cp2 = st.columns(2)
    with cp1:
        p1_name = st.text_input("First Player (Last Name):", key="compare_p1")
    with cp2:
        p2_name = st.text_input("Second Player (Last Name):", key="compare_p2")

    if p1_name and p2_name:
        if st.button("Run Comparison Graph", key="compare_btn"):
            try:
                # Verifying if both players belong to our selected sport view before passing payloads
                p1_check = df_filtered[df_filtered["last_name"].str.lower() == p1_name.lower()]
                p2_check = df_filtered[df_filtered["last_name"].str.lower() == p2_name.lower()]

                if p1_check.empty or p2_check.empty:
                    st.error(f"One or both players were not found inside the active {selected_sport} registry.")
                else:
                    response = requests.post(f"{BACKEND_URL}/compare", json={"p1": p1_name, "p2": p2_name})
                    if response.status_code == 200:
                        comp_data = response.json()
                        df = pd.DataFrame(comp_data)

                        # Adjust labels for Basketball or Football views
                        if selected_sport == "Basketballer":
                            df["metrics"] = df["metrics"].replace(
                                {"Goals": "Points Scored", "Goals per 90": "Points per 90"})

                        st.subheader("Performance Volumetric Breakdown")
                        fig = px.bar(df, x="metrics", y=[p1_name, p2_name], barmode="group",
                                     title=f"Comparison: {p1_name} vs {p2_name}",
                                     color_discrete_sequence=["#7A1FA2", "#0097A7"])
                        st.plotly_chart(fig, use_container_width=True)

                        st.write("---")
                        comp_graph_col1, comp_graph_col2 = st.columns(2)

                        with comp_graph_col1:
                            radar_filter = df[~df["metrics"].str.contains("per 90")]
                            df_radar = radar_filter.melt(id_vars="metrics", var_name="Player", value_name="Volume")

                            fig_radar = px.line_polar(df_radar, r="Volume", theta="metrics", color="Player",
                                                      line_close=True,
                                                      title="Volume Coverage Profile",
                                                      color_discrete_sequence=["#7A1FA2", "#0097A7"])
                            fig_radar.update_traces(fill="toself")
                            st.plotly_chart(fig_radar, use_container_width=True)

                        with comp_graph_col2:
                            p1_g = df[df["metrics"].isin(["Goals", "Points Scored"])][p1_name].values[0]
                            p2_g = df[df["metrics"].isin(["Goals", "Points Scored"])][p2_name].values[0]

                            if (p1_g + p2_g) > 0:
                                share_df = pd.DataFrame({
                                    "Player": [p1_name, p2_name],
                                    "Total Output": [p1_g, p2_g]
                                })
                                label_share = "Combined Point Share Matrix" if selected_sport == "Basketballer" else "Combined Goal Share Matrix"
                                fig_share = px.pie(share_df, names="Player", values="Total Output", hole=0.5,
                                                   title=label_share,
                                                   color_discrete_sequence=["#7A1FA2", "#0097A7"])
                                st.plotly_chart(fig_share, use_container_width=True)
                            else:
                                st.info("Target players maintain zero metrics output, skipping ratio projection share.")
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
                p_check = df_filtered[df_filtered["last_name"].str.lower() == target_player.lower()]
                if p_check.empty:
                    st.error(f"Target player was not found inside the active {selected_sport} structural profile.")
                else:
                    response = requests.get(f"{BACKEND_URL}/player/{target_player}/predict")
                    if response.status_code == 200:
                        trend_data = response.json()
                        df_trend = pd.DataFrame(trend_data)

                        y_lbls = ["historical_goals", "predicted_trend"]
                        if selected_sport == "Basketballer":
                            df_trend = df_trend.rename(columns={"historical_goals": "historical_points"})
                            y_lbls = ["historical_points", "predicted_trend"]

                        fig_trend = px.line(df_trend, x="games", y=y_lbls,
                                            labels={"value": "Volume Impact", "variable": "Data Type"},
                                            title=f"Performance Trajectory Forecast for {target_player}")
                        st.plotly_chart(fig_trend, use_container_width=True)
                    else:
                        st.error("Could not compute trend line for this player.")
            except requests.exceptions.ConnectionError:
                st.error("Backend unreachable.")

with tab_raw_analytics:
    st.header(f"Aggregated {selected_sport} Roster Analytics")
    st.caption("Real-time automated visualizations mapping filtered dataset metrics.")

    if not df_filtered.empty:
        df_filtered["full_name"] = df_filtered["first_name"] + " " + df_filtered["last_name"]

        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            pie_title = "Squad Goal Share Distribution" if selected_sport == "Footballer" else "Squad Point Share Distribution"
            fig_pie = px.pie(df_filtered, names="full_name", values="goals", title=pie_title, hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)

        with row1_col2:
            df_sorted = df_filtered.sort_values(by="goals", ascending=False)
            bar_title = "Goal vs Assist Production Rankings" if selected_sport == "Footballer" else "Points vs Assist Production Rankings"
            fig_bar = px.bar(df_sorted, x="full_name", y=["goals", "assists"], barmode="group", title=bar_title)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.write("---")

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            df_pos = df_filtered.groupby("position").agg({"goals": "sum", "assists": "sum"}).reset_index()
            fig_pos = px.bar(df_pos, x="position", y=["goals", "assists"], barmode="group",
                             title="Attacking Volume Breakdown by Position Group")
            st.plotly_chart(fig_pos, use_container_width=True)

        with row2_col2:
            df_team = df_filtered.groupby("team")["goals"].sum().reset_index().sort_values(by="goals", ascending=False)
            standings_title = "Total Club Goals Standings" if selected_sport == "Footballer" else "Total Club Points Standings"
            fig_team = px.bar(df_team, x="team", y="goals", title=standings_title, color="team")
            st.plotly_chart(fig_team, use_container_width=True)

        st.write("---")

        row3_col1, row3_col2 = st.columns(2)
        with row3_col1:
            scatter_title = "Minutes Logged vs Goals Converted" if selected_sport == "Footballer" else "Minutes Logged vs Points Scored"
            fig_scatter = px.scatter(df_filtered, x="minutes_played", y="goals", color="position",
                                     size="matches_played", hover_name="full_name", title=scatter_title)
            st.plotly_chart(fig_scatter, use_container_width=True)

        with row3_col2:
            fig_nat = px.histogram(df_filtered, x="nationality",
                                   title="Roster Cultural Demographic Composition Matrix", color="position")
            st.plotly_chart(fig_nat, use_container_width=True)
    else:
        st.info(
            f"Add records or check backend server data inside database files to visualize {selected_sport} metrics.")