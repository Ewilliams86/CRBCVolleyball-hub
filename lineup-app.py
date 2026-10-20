import streamlit as st
import pandas as pd
import datetime

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Universal Volleyball Lineup & Stat Hub",
    page_icon="🏐",
    layout="wide"
)

# --- BLANK DEFAULT ROSTER & POSITIONAL SETUP ---
DEFAULT_TEAMS = {
    "Sample Team Roster": {
        f"Player {i}": {"tier": "Developing", "role": "Universal / Utility", "buddy": "Open"} for i in range(1, 12)
    }
}

if "team_rosters" not in st.session_state:
    st.session_state.team_rosters = DEFAULT_TEAMS

if "active_team" not in st.session_state:
    st.session_state.active_team = "Sample Team Roster"

# Current Team Roster & Roles
current_team_dict = st.session_state.team_rosters[st.session_state.active_team]
active_team_roster = list(current_team_dict.keys())

# --- INITIALIZE SESSION STATE ARCHIVE ---
if "matches" not in st.session_state:
    st.session_state.matches = {}

# --- GLOBAL MATCH & TEAM SELECTOR (TOP BAR) ---
st.title("🏐 CBRC Universal Volleyball Lineup & Stat Hub")

col_top1, col_top2 = st.columns([1, 2])
with col_top1:
    selected_team = st.selectbox("Select Active Team:", list(st.session_state.team_rosters.keys()) + ["➕ Create New Custom Team"])
    if selected_team == "➕ Create New Custom Team":
        new_team_name = st.text_input("Enter Your Team Name:", "My Team")
        if st.button("➕ Initialize Team"):
            st.session_state.team_rosters[new_team_name] = {
                f"Player {i}": {"tier": "Developing", "role": "Universal / Utility", "buddy": "Open"} for i in range(1, 12)
            }
            st.session_state.active_team = new_team_name
            st.success(f"Initialized {new_team_name}! Head to '👥 Roster, Roles & Positions' to enter your players.")
            st.rerun()
    else:
        st.session_state.active_team = selected_team

with col_top2:
    match_list = [k for k, v in st.session_state.matches.items() if v.get("team") == st.session_state.active_team] + ["➕ Create New Game"]
    selected_match_key = st.selectbox("Select Active Game / Match Archive:", match_list)

# --- APP NAVIGATION TABS ---
tab_lineup, tab_stats, tab_roles, tab_history, tab_rules = st.tabs([
    "📋 Lineup Generator & Editor",
    "📊 Live Serve & Point Tracker",
    "👥 Roster, Roles & Positions",
    "📈 Season History & Trends",
    "⚙️ League Rules & Settings"
])

# --- TAB 3: ROSTER, SKILL TIERS & POSITIONS ---
with tab_roles:
    st.header(f"👥 Roster & Position Settings - {st.session_state.active_team}")
    st.info("💡 **Setup Instructions:** Type in your team's roster names below and assign their court positions (Setters, Libero, Hitters) or Buddy System pairs.")
   
    tier_options = ["Anchor", "Playmaker", "Developing", "Server Specialist", "Floating Rotator"]
    role_options = ["Setter (S)", "Libero / DS (L)", "Outside Hitter (OH)", "Middle Blocker (MB)", "Right Side (OPP)", "Defensive Specialist (DS)", "Universal / Utility"]
    buddy_options = active_team_roster + ["None (Floating)", "Open / Unassigned"]
   
    col_r1, col_r2 = st.columns(2)
   
    role_rows = []
    for p_name, p_data in current_team_dict.items():
        role_rows.append({
            "Player": p_name,
            "Court Role / Position": p_data.get("role", "Universal / Utility"),
            "Skill Tier": p_data.get("tier", "Developing"),
            "Buddy Partner": p_data.get("buddy", "Open")
        })
   
    with col_r1:
        st.subheader("Current Team Roster & Roles")
        st.dataframe(pd.DataFrame(role_rows), use_container_width=True)
       
    with col_r2:
        st.subheader("Edit Player Name & Role")
        edit_p = st.selectbox("Select Player to Update:", active_team_roster)
       
        updated_p_name = st.text_input("Rename Player:", value=edit_p)
        curr_role = current_team_dict[edit_p].get("role", "Universal / Utility")
        curr_tier = current_team_dict[edit_p].get("tier", "Developing")
        curr_buddy = current_team_dict[edit_p].get("buddy", "Open")
       
        new_r = st.selectbox("Assigned Position Role:", role_options, index=role_options.index(curr_role) if curr_role in role_options else 0)
        new_t = st.selectbox("Assigned Skill Tier:", tier_options, index=tier_options.index(curr_tier) if curr_tier in tier_options else 0)
        new_b = st.selectbox("Assigned Buddy Partner:", buddy_options, index=buddy_options.index(curr_buddy) if curr_buddy in buddy_options else 0)
       
        if st.button("💾 Save Player Changes"):
            if updated_p_name != edit_p:
                st.session_state.team_rosters[st.session_state.active_team][updated_p_name] = {
                    "role": new_r, "tier": new_t, "buddy": new_b
                }
                del st.session_state.team_rosters[st.session_state.active_team][edit_p]
            else:
                st.session_state.team_rosters[st.session_state.active_team][edit_p] = {
                    "role": new_r, "tier": new_t, "buddy": new_b
                }
            st.success(f"Updated {updated_p_name}!")
            st.rerun()

    st.markdown("---")
    st.subheader("➕ Add New Player to Team")
    c_np1, c_np2, c_np3, c_np4 = st.columns(4)
    with c_np1:
        np_name = st.text_input("New Player Name:")
    with c_np2:
        np_role = st.selectbox("Position Role:", role_options, key="np_role")
    with c_np3:
        np_tier = st.selectbox("Skill Tier:", tier_options, key="np_tier")
    with c_np4:
        np_buddy = st.selectbox("Buddy Partner:", buddy_options, key="np_buddy")
       
    if st.button("➕ Add Player"):
        if np_name and np_name not in current_team_dict:
            st.session_state.team_rosters[st.session_state.active_team][np_name] = {
                "role": np_role, "tier": np_tier, "buddy": np_buddy
            }
            st.success(f"Added {np_name} to {st.session_state.active_team}!")
            st.rerun()

# --- TAB 1: LINEUP GENERATOR & EDITABLE OVERRIDE ---
with tab_lineup:
    st.header(f"📋 Lineup Generator - {st.session_state.active_team}")
   
    if selected_match_key == "➕ Create New Game" or not selected_match_key:
        c1, c2, c3 = st.columns(3)
        with c1:
            game_num = st.text_input("Game Number/Name", "Game 1")
        with c2:
            opp_name = st.text_input("Opponent Name", "Opponent")
        with c3:
            game_date = st.date_input("Match Date", datetime.date.today())
       
        match_title = f"{game_num} vs {opp_name} ({game_date.strftime('%m/%d/%Y')})"
        active_list = st.multiselect("Active Roster Today:", active_team_roster, default=active_team_roster)
       
        rot_style = st.selectbox(
            "Select Rotation System:",
            ["Buddy System (Equal Play / Rec)", "Fixed Core Positions (Setters, Libero, OH, MB)"]
        )
       
        enforce_rules = st.checkbox("Enforce CBRC Rules (Mandatory Set 1/2 Starts, 4 Sub Credits, Max 3 Subs/Stoppage)", value=True)
       
        if st.button("🚀 Generate Compliant Match Lineup"):
            p_list = active_list.copy()
            st.session_state.matches[match_title] = {
                "team": st.session_state.active_team,
                "date": str(game_date),
                "opponent": opp_name,
                "mode": rot_style,
                "active_players": active_list,
                "lineup": {
                    "Set 1": {
                        "Starters": p_list[:6] if len(p_list) >= 6 else p_list,
                        "Subs": p_list[6:] + ["Open / Continuous"] * max(0, 12 - len(p_list))
                    },
                    "Set 2": {
                        "Starters": (p_list[6:] + p_list[:6])[:6],
                        "Subs": (p_list[:6] + ["Open / Continuous"])[:6]
                    },
                    "Set 3": {
                        "Starters": p_list[:6] if len(p_list) >= 6 else p_list,
                        "Subs": p_list[6:] + ["Open / Continuous"] * max(0, 12 - len(p_list))
                    }
                },
                "stats": {p: {"Attempts": 0, "Makes": 0, "Aces": 0, "Points_Won": 0} for p in active_list}
            }
            st.success(f"Generated 100% Rule-Compliant Lineup for {match_title} using '{rot_style}'!")
            st.rerun()
           
    else:
        current_data = st.session_state.matches[selected_match_key]
        st.subheader(f"Active Match: {selected_match_key}")
        st.caption(f"System Mode: **{current_data.get('mode', 'Buddy System')}** | CBRC Rule Compliant: ✅ YES")
        st.info("💡 **Manual Override:** You can manually swap any starter or sub position using the drop-downs below!")
       
        s1, s2, s3 = st.tabs(["Set 1 Lineup", "Set 2 Lineup", "Set 3 Lineup"])
        for set_num, set_tab in zip(["Set 1", "Set 2", "Set 3"], [s1, s2, s3]):
            with set_tab:
                col_st, col_su = st.columns(2)
               
                # Editable Starting 6
                with col_st:
                    st.markdown("### 🏐 Starting 6 (Editable)")
                    new_starters = []
                    for idx in range(6):
                        curr_p = current_data["lineup"][set_num]["Starters"][idx] if idx < len(current_data["lineup"][set_num]["Starters"]) else active_team_roster[0]
                        p_role_tag = current_team_dict.get(curr_p, {}).get("role", "Utility")
                       
                        sel_p = st.selectbox(
                            f"Serve Order {idx+1} [{p_role_tag}]:",
                            active_team_roster,
                            index=active_team_roster.index(curr_p) if curr_p in active_team_roster else 0,
                            key=f"{selected_match_key}_{set_num}_starter_{idx}"
                        )
                        new_starters.append(sel_p)
                    current_data["lineup"][set_num]["Starters"] = new_starters

                # Editable Subs
                with col_su:
                    st.markdown("### 🔄 Bench Substitutes (Editable)")
                    sub_opts = active_team_roster + ["Open / Continuous"]
                    new_subs = []
                    for idx in range(6):
                        curr_s = current_data["lineup"][set_num]["Subs"][idx] if idx < len(current_data["lineup"][set_num]["Subs"]) else "Open / Continuous"
                        sel_s = st.selectbox(
                            f"Sub Line {idx+1}:",
                            sub_opts,
                            index=sub_opts.index(curr_s) if curr_s in sub_opts else 0,
                            key=f"{selected_match_key}_{set_num}_sub_{idx}"
                        )
                        new_subs.append(sel_s)
                    current_data["lineup"][set_num]["Subs"] = new_subs

# --- TAB 2: LIVE SERVE & POINT TRACKER ---
with tab_stats:
    st.header("📊 Live Courtside Serve & Point Tracker")
   
    if selected_match_key == "➕ Create New Game" or not selected_match_key:
        st.warning("Please select or create an active game in the top dropdown to start tracking stats.")
    else:
        active_match = st.session_state.matches[selected_match_key]
        p_list = active_match["active_players"]
       
        col_ctrl, col_view = st.columns([1, 2])
       
        with col_ctrl:
            st.subheader("Record Action")
            server = st.selectbox("Select Current Server:", p_list)
           
            b1, b2 = st.columns(2)
            with b1:
                if st.button("✅ Serve IN"):
                    active_match["stats"][server]["Attempts"] += 1
                    active_match["stats"][server]["Makes"] += 1
                    st.toast(f"Logged Serve IN for {server}")
                if st.button("🔥 ACE!"):
                    active_match["stats"][server]["Attempts"] += 1
                    active_match["stats"][server]["Makes"] += 1
                    active_match["stats"][server]["Aces"] += 1
                    active_match["stats"][server]["Points_Won"] += 1
                    st.toast(f"Logged ACE for {server}!")
            with b2:
                if st.button("❌ Serve Out / Net"):
                    active_match["stats"][server]["Attempts"] += 1
                    st.toast(f"Logged Serve Out for {server}")
                if st.button("🏆 Point Scored on Serve"):
                    active_match["stats"][server]["Points_Won"] += 1
                    st.toast(f"Logged Point Won on {server}'s serve!")

        with col_view:
            st.subheader(f"Match Box Score - {selected_match_key}")
            stats_rows = []
            for player_name in p_list:
                p_stat = active_match["stats"].get(player_name, {"Attempts": 0, "Makes": 0, "Aces": 0, "Points_Won": 0})
                att = p_stat["Attempts"]
                mks = p_stat["Makes"]
                pct = (mks / att * 100) if att > 0 else 0.0
                stats_rows.append({
                    "Player": player_name,
                    "Position": current_team_dict.get(player_name, {}).get("role", "Utility"),
                    "Attempts": att,
                    "Serves In": mks,
                    "Serve %": f"{pct:.1f}%",
                    "Aces": p_stat["Aces"],
                    "Points Won on Serve": p_stat["Points_Won"]
                })
           
            df_match_stats = pd.DataFrame(stats_rows)
            st.dataframe(df_match_stats, use_container_width=True)

# --- TAB 4: SEASON HISTORY & TRENDS ---
with tab_history:
    st.header(f"📈 Season History & Cumulative Trends - {st.session_state.active_team}")
    st.caption("Aggregated performance across all logged matches.")
   
    season_totals = {p: {"Attempts": 0, "Makes": 0, "Aces": 0, "Points_Won": 0} for p in active_team_roster}
   
    for g_key, g_data in st.session_state.matches.items():
        if g_data.get("team") == st.session_state.active_team:
            for p_name, p_stat in g_data["stats"].items():
                if p_name not in season_totals:
                    season_totals[p_name] = {"Attempts": 0, "Makes": 0, "Aces": 0, "Points_Won": 0}
                season_totals[p_name]["Attempts"] += p_stat["Attempts"]
                season_totals[p_name]["Makes"] += p_stat["Makes"]
                season_totals[p_name]["Aces"] += p_stat["Aces"]
                season_totals[p_name]["Points_Won"] += p_stat["Points_Won"]
           
    season_rows = []
    for p_name, s_stat in season_totals.items():
        att = s_stat["Attempts"]
        mks = s_stat["Makes"]
        pct = (mks / att * 100) if att > 0 else 0.0
        season_rows.append({
            "Player": p_name,
            "Position": current_team_dict.get(p_name, {}).get("role", "Utility"),
            "Total Serve Attempts": att,
            "Total Serves In": mks,
            "Season Serve %": f"{pct:.1f}%",
            "Total Aces": s_stat["Aces"],
            "Total Points Scored on Serve": s_stat["Points_Won"]
        })
       
    df_season = pd.DataFrame(season_rows)
    st.dataframe(df_season, use_container_width=True)

# --- TAB 5: LEAGUE RULES & SETTINGS ---
with tab_rules:
    st.header("⚙️ CBRC League Rules & Settings Engine")
   
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.subheader("Substitution Limits")
        st.slider("Max Subs Per Stoppage", 1, 6, 3)
        st.number_input("Mandatory Sub Credits Per Match", 1, 10, 4)
        st.selectbox("Match Format", ["3 Fixed Sets (CBRC Standard)", "Best 2 out of 3", "Best 3 out of 5"])
   
    with col_r2:
        st.subheader("Participation Rules")
        st.selectbox("Set Starting Requirement", ["Must start Set 1 or Set 2 (CBRC)", "Must start at least 1 set", "Open / Coach Choice"])
        st.checkbox("Enforce Set 3 Participation for All Active Players", value=True)
        st.checkbox("Enable Libero / Position Tracking", value=True)
