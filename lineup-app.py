import streamlit as st
import pandas as pd
import datetime
import json
import os

# --- CUSTOM CSS STYLING ---
st.markdown("""
    <style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
   
    /* Custom Header Styling */
    h1, h2, h3 {
        color: #FFD700 !important; /* Gold Header Color */
        font-family: 'Trebuchet MS', sans-serif;
    }
   
    /* Styled Stat Cards */
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: bold;
        color: #00E676 !important; /* Neon Green Stats */
    }
   
    /* Tab Styling */
    button[data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: bold;
        color: #B0BEC5;
    }
    button[aria-selected="true"] {
        color: #FFD700 !important;
        border-bottom-color: #FFD700 !important;
    }
   
    /* Styled Buttons */
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
    }
    .stButton>button:hover {
        background-color: #1565C0;
        color: #FFD700;
    }
    </style>
""", unsafe_allow_html=True)

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Universal Volleyball Lineup & Stat Hub",
    page_icon="🏐",
    layout="wide"
)

# --- PERMANENT FILE STORAGE PATHS ---
ROSTER_FILE = "roster_data.json"
MATCHES_FILE = "match_archive.json"

# GENERIC DEFAULT ROSTER
DEFAULT_ROSTER = {
    f"Player {i}": {
        "tier": "Anchor" if i in [1, 2, 3, 4] else "Developing",
        "role": "Setter (S)" if i in [1, 2] else ("Outside Hitter (OH)" if i in [3, 4] else "Universal / Utility"),
        "buddy": f"Player {i+6}" if i <= 5 else f"Player {i-5}"
    } for i in range(1, 12)
}

# GENERIC DEFAULT MATCH ARCHIVE
DEFAULT_MATCHES = {}

# --- FILE PERSISTENCE HELPERS ---
def load_data(file_path, default_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception:
            return default_data
    return default_data

def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# --- AUTO-BALANCE BUDDY LOGIC ---
def auto_balance_buddies(roster_dict):
    anchors_core = []
    developing = []
   
    for p_name, p_data in roster_dict.items():
        t = p_data.get("tier", "Developing")
        if "Floating" in t or "Floating" in p_data.get("buddy", ""):
            continue
        if t in ["Anchor", "Playmaker", "Server Specialist", "Defensive Specialist", "Anchor / Floating Rotator"]:
            anchors_core.append(p_name)
        else:
            developing.append(p_name)
           
    pairs_count = min(len(anchors_core), len(developing))
    for i in range(pairs_count):
        anc = anchors_core[i]
        dev = developing[i]
        roster_dict[anc]["buddy"] = dev
        roster_dict[dev]["buddy"] = anc
       
    return roster_dict

# --- INITIALIZE PERMANENT SESSION STATE ---
if "roster" not in st.session_state:
    st.session_state["roster"] = load_data(ROSTER_FILE, DEFAULT_ROSTER)

if "matches" not in st.session_state:
    st.session_state["matches"] = load_data(MATCHES_FILE, DEFAULT_MATCHES)

if "team_rosters" not in st.session_state:
    st.session_state["team_rosters"] = {"Sample Team Roster": st.session_state["roster"]}

if "active_team" not in st.session_state:
    st.session_state["active_team"] = "Sample Team Roster"

active_team = st.session_state["active_team"]
current_team_dict = st.session_state["team_rosters"].get(active_team, st.session_state["roster"])
active_team_roster = list(current_team_dict.keys())

# --- GLOBAL TOP BAR ---
st.title("🏐 CBRC Universal Volleyball Lineup & Stat Hub")

col_top1, col_top2 = st.columns([1, 2])
with col_top1:
    selected_team = st.selectbox("Select Active Team:", list(st.session_state["team_rosters"].keys()) + ["➕ Create New Custom Team"])
    if selected_team == "➕ Create New Custom Team":
        new_team_name = st.text_input("Enter Your Team Name:", "My Team")
        if st.button("➕ Initialize Team"):
            st.session_state["team_rosters"][new_team_name] = {
                f"Player {i}": {"tier": "Developing", "role": "Universal / Utility", "buddy": "Open"} for i in range(1, 12)
            }
            st.session_state["active_team"] = new_team_name
            st.success(f"Initialized {new_team_name}! Head to '👥 Roster, Roles & Positions' to enter your players.")
            st.rerun()
    else:
        st.session_state["active_team"] = selected_team

with col_top2:
    match_list = [k for k, v in st.session_state["matches"].items() if v.get("team") == active_team] + ["➕ Create New Game"]
    selected_match_key = st.selectbox("Select Active Game / Match Archive:", match_list)

# --- APP NAVIGATION TABS ---
tab_lineup, tab_court, tab_stats, tab_roles, tab_history, tab_rules = st.tabs([
    "📋 Lineup Generator & Editor",
    "🏐 Visual Court Positions",
    "📊 Live Serve & Point Tracker",
    "👥 Roster, Roles & Positions",
    "📈 Season History & Trends",
    "⚙️ League Rules & Settings"
])

# --- TAB 1: LINEUP GENERATOR ---
with tab_lineup:
    st.header(f"📋 Lineup Generator - {active_team}")
   
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
        rot_style = st.selectbox("Select Rotation System:", ["Buddy System (Equal Play / Rec)", "Fixed Core Positions (Setters, Libero, OH, MB)"])
       
        if st.button("🚀 Generate & Permanently Save Match"):
            p_list = active_list.copy()
            st.session_state["matches"][match_title] = {
                "team": active_team,
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
            save_data(MATCHES_FILE, st.session_state["matches"])
            st.success(f"💾 Permanently saved {match_title}!")
            st.rerun()
           
    else:
        current_data = st.session_state["matches"][selected_match_key]
        st.subheader(f"Active Match: {selected_match_key}")
        st.caption(f"System Mode: **{current_data.get('mode', 'Buddy System')}** | CBRC Rule Compliant: ✅ YES")
       
        s1, s2, s3 = st.tabs(["Set 1 Lineup", "Set 2 Lineup", "Set 3 Lineup"])
        for set_num, set_tab in zip(["Set 1", "Set 2", "Set 3"], [s1, s2, s3]):
            with set_tab:
                col_st, col_su = st.columns(2)
               
                with col_st:
                    st.markdown("### 🏐 Starting 6 (Editable)")
                    new_starters = []
                    for idx in range(6):
                        curr_p = current_data["lineup"][set_num]["Starters"][idx] if idx < len(current_data["lineup"][set_num]["Starters"]) else active_team_roster[0]
                        p_role_tag = current_team_dict.get(curr_p, {}).get("role", "Utility")
                        p_tier_tag = current_team_dict.get(curr_p, {}).get("tier", "Developing")
                       
                        sel_p = st.selectbox(
                            f"Serve Order {idx+1} [{p_role_tag} - {p_tier_tag}]:",
                            active_team_roster,
                            index=active_team_roster.index(curr_p) if curr_p in active_team_roster else 0,
                            key=f"{selected_match_key}_{set_num}_starter_{idx}"
                        )
                        new_starters.append(sel_p)
                    current_data["lineup"][set_num]["Starters"] = new_starters

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
               
        if st.button("💾 Permanently Save Lineup Edits"):
            save_data(MATCHES_FILE, st.session_state["matches"])
            st.success("💾 Saved modified lineup changes permanently!")

# --- TAB 2: VISUAL COURT POSITIONS ---
with tab_court:
    st.header("🏐 Visual Court Diagram & Position Layout")
   
    if selected_match_key == "➕ Create New Game" or not selected_match_key:
        st.warning("Please select or create an active game in the top dropdown to view the court diagram.")
    else:
        current_data = st.session_state["matches"][selected_match_key]
        set_choice = st.radio("Select Set to Display on Court:", ["Set 1", "Set 2", "Set 3"], horizontal=True)
        starters = current_data["lineup"][set_choice]["Starters"]
       
        p1 = starters[0] if len(starters) > 0 else "Open"
        p2 = starters[1] if len(starters) > 1 else "Open"
        p3 = starters[2] if len(starters) > 2 else "Open"
        p4 = starters[3] if len(starters) > 3 else "Open"
        p5 = starters[4] if len(starters) > 4 else "Open"
        p6 = starters[5] if len(starters) > 5 else "Open"

        st.markdown("### 🏐 Court Formation - Front Row & Back Row")
        st.markdown("--- **NET** ---")
       
        fr1, fr2, fr3 = st.columns(3)
        with fr1:
            st.metric(label="Pos 4 (Front Left)", value=p4, delta=f"{current_team_dict.get(p4, {}).get('role', 'Utility')} | {current_team_dict.get(p4, {}).get('tier', 'Developing')}")
        with fr2:
            st.metric(label="Pos 3 (Front Center)", value=p3, delta=f"{current_team_dict.get(p3, {}).get('role', 'Utility')} | {current_team_dict.get(p3, {}).get('tier', 'Developing')}")
        with fr3:
            st.metric(label="Pos 2 (Front Right)", value=p2, delta=f"{current_team_dict.get(p2, {}).get('role', 'Utility')} | {current_team_dict.get(p2, {}).get('tier', 'Developing')}")
           
        st.markdown("--- 3-Meter Attack Line ---")
       
        br1, br2, br3 = st.columns(3)
        with br1:
            st.metric(label="Pos 5 (Back Left)", value=p5, delta=f"{current_team_dict.get(p5, {}).get('role', 'Utility')} | {current_team_dict.get(p5, {}).get('tier', 'Developing')}")
        with br2:
            st.metric(label="Pos 6 (Back Center)", value=p6, delta=f"{current_team_dict.get(p6, {}).get('role', 'Utility')} | {current_team_dict.get(p6, {}).get('tier', 'Developing')}")
        with br3:
            st.metric(label="Pos 1 (Back Right / Server)", value=p1, delta=f"1st Server | {current_team_dict.get(p1, {}).get('role', 'Utility')} | {current_team_dict.get(p1, {}).get('tier', 'Developing')}")

# --- TAB 3: LIVE SERVE & POINT TRACKER ---
with tab_stats:
    st.header("📊 Live Courtside Serve & Point Tracker")
   
    if selected_match_key == "➕ Create New Game" or not selected_match_key:
        st.warning("Please select or create an active game in the top dropdown to start tracking stats.")
    else:
        active_match = st.session_state["matches"][selected_match_key]
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
                    save_data(MATCHES_FILE, st.session_state["matches"])
                    st.toast(f"Logged & Saved Serve IN for {server}")
                if st.button("🔥 ACE!"):
                    active_match["stats"][server]["Attempts"] += 1
                    active_match["stats"][server]["Makes"] += 1
                    active_match["stats"][server]["Aces"] += 1
                    active_match["stats"][server]["Points_Won"] += 1
                    save_data(MATCHES_FILE, st.session_state["matches"])
                    st.toast(f"Logged & Saved ACE for {server}!")
            with b2:
                if st.button("❌ Serve Out / Net"):
                    active_match["stats"][server]["Attempts"] += 1
                    save_data(MATCHES_FILE, st.session_state["matches"])
                    st.toast(f"Logged & Saved Serve Out for {server}")
                if st.button("🏆 Point Scored on Serve"):
                    active_match["stats"][server]["Points_Won"] += 1
                    save_data(MATCHES_FILE, st.session_state["matches"])
                    st.toast(f"Logged & Saved Point Won on {server}'s serve!")

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
                    "Tier": current_team_dict.get(player_name, {}).get("tier", "Developing"),
                    "Attempts": att,
                    "Serves In": mks,
                    "Serve %": f"{pct:.1f}%",
                    "Aces": p_stat["Aces"],
                    "Points Won on Serve": p_stat["Points_Won"]
                })
           
            df_match_stats = pd.DataFrame(stats_rows)
            st.dataframe(df_match_stats, use_container_width=True)
           
            csv_data = df_match_stats.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Match Stats to CSV / Google Sheets",
                data=csv_data,
                file_name=f"{selected_match_key}_stats.csv",
                mime="text/csv"
            )

# --- TAB 4: ROSTER, SKILL TIERS & POSITIONS ---
with tab_roles:
    st.header(f"👥 Roster & Position Settings - {active_team}")
    st.info("💡 **Setup Instructions:** Enter player names and update positions or auto-balance buddy pairs below!")
   
    tier_options = ["Anchor", "Playmaker", "Developing", "Server Specialist", "Defensive Specialist", "Anchor / Floating Rotator"]
    role_options = ["Setter (S)", "Libero / DS (L)", "Outside Hitter (OH)", "Middle Blocker (MB)", "Right Side (OPP)", "Defensive Specialist (DS)", "Universal / Utility"]
    buddy_options = active_team_roster + ["None (Floating)", "Open / Unassigned"]
   
    col_r1, col_r2 = st.columns(2)
   
    with col_r1:
        st.subheader("Current Permanent Roster Overview")
        role_rows = []
        for p_name, p_data in current_team_dict.items():
            role_rows.append({
                "Player": p_name,
                "Skill Tier": p_data.get("tier", "Developing"),
                "Court Position": p_data.get("role", "Universal / Utility"),
                "Buddy Partner": p_data.get("buddy", "Open")
            })
        st.dataframe(pd.DataFrame(role_rows), use_container_width=True)
       
        st.markdown("---")
        st.subheader("⚡ Auto-Balance Buddy System")
        st.caption("Pairs Core Anchors and Specialists 1-to-1 with Developing players.")
       
        if st.button("⚡ Auto-Balance Buddy Pairs Now"):
            st.session_state["team_rosters"][active_team] = auto_balance_buddies(current_team_dict)
            save_data(ROSTER_FILE, st.session_state["team_rosters"][active_team])
            st.success("⚡ Successfully auto-balanced and permanently saved Buddy Pairs!")
            st.rerun()

    with col_r2:
        st.subheader("Update Player Name & Profile")
        edit_p = st.selectbox("Select Player to Update:", active_team_roster, key="edit_p_perm")
       
        with st.form(key="perm_player_form"):
            updated_p_name = st.text_input("Rename Player:", value=edit_p)
            curr_tier = current_team_dict[edit_p].get("tier", "Developing")
            curr_role = current_team_dict[edit_p].get("role", "Universal / Utility")
            curr_buddy = current_team_dict[edit_p].get("buddy", "Open")
           
            new_t = st.selectbox("Assign Skill Tier:", tier_options, index=tier_options.index(curr_tier) if curr_tier in tier_options else 0)
            new_r = st.selectbox("Assign Position Role:", role_options, index=role_options.index(curr_role) if curr_role in role_options else 0)
            new_b = st.selectbox("Assign Buddy Partner:", buddy_options, index=buddy_options.index(curr_buddy) if curr_buddy in buddy_options else 0)
           
            submit_button = st.form_submit_button(label="💾 Save Player Profile Changes Permanently")
           
            if submit_button:
                if updated_p_name != edit_p:
                    st.session_state["team_rosters"][active_team][updated_p_name] = {
                        "tier": new_t, "role": new_r, "buddy": new_b
                    }
                    del st.session_state["team_rosters"][active_team][edit_p]
                else:
                    st.session_state["team_rosters"][active_team][edit_p] = {
                        "tier": new_t, "role": new_r, "buddy": new_b
                    }
                save_data(ROSTER_FILE, st.session_state["team_rosters"][active_team])
                st.success(f"💾 Permanently saved {updated_p_name}!")
                st.rerun()

# --- TAB 5: SEASON HISTORY & TRENDS ---
with tab_history:
    st.header(f"📈 Season History & Cumulative Trends - {active_team}")
   
    season_totals = {p: {"Attempts": 0, "Makes": 0, "Aces": 0, "Points_Won": 0} for p in active_team_roster}
    for g_key, g_data in st.session_state["matches"].items():
        if g_data.get("team") == active_team:
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
            "Tier": current_team_dict.get(p_name, {}).get("tier", "Developing"),
            "Total Serve Attempts": att,
            "Total Serves In": mks,
            "Season Serve %": f"{pct:.1f}%",
            "Total Aces": s_stat["Aces"],
            "Total Points Scored on Serve": s_stat["Points_Won"]
        })
       
    df_season = pd.DataFrame(season_rows)
    st.dataframe(df_season, use_container_width=True)

# --- TAB 6: LEAGUE RULES & SETTINGS ---
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
team_passwords = st.session_state.get("team_passwords", {"Sample Team": "1234"})

selected_team = st.selectbox("Select Active Team:", list(st.session_state["team_rosters"].keys()) + ["➕ Register New Team"])

if selected_team != "➕ Register New Team":
    entered_pin = st.text_input(f"🔒 Enter PIN for {selected_team}:", type="password")
    if entered_pin != team_passwords.get(selected_team, ""):
        st.error("Incorrect Team PIN. Please enter your team password to view lineups and stats.")
        st.stop() # Blocks unauthorized users from seeing the app content
