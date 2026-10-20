import streamlit as st
import pandas as pd
import datetime
import json
import os

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="CBRC Universal Volleyball Hub",
    page_icon="🏐",
    layout="wide"
)

# --- CLEAN EXECUTIVE SPORTS STYLING ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: radial-gradient(#334155 1px, transparent 1px);
        background-size: 24px 24px;
        opacity: 0.15;
        pointer-events: none;
    }
    h1, h2, h3 { color: #F8FAFC !important; font-weight: 700; }
    .stMarkdown h3 { color: #38BDF8 !important; font-size: 1.1rem !important; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 600; color: #38BDF8 !important; }
    div[data-testid="stMetric"] { background-color: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 10px; padding: 12px 16px; }
    button[data-baseweb="tab"] { font-size: 14px !important; font-weight: 600; color: #94A3B8; }
    button[aria-selected="true"] { color: #38BDF8 !important; border-bottom-color: #38BDF8 !important; }
    .stButton>button { background-color: #0284C7; color: #FFFFFF; font-weight: 600; border-radius: 6px; border: none; padding: 6px 14px; }
    </style>
""", unsafe_allow_html=True)

# --- PERMANENT FILE PATHS ---
ROSTER_FILE = "roster_data.json"
MATCHES_FILE = "match_archive.json"
PASSWORDS_FILE = "team_passwords.json"

DEFAULT_ROSTER = {
    f"Player {i}": {
        "tier": "Anchor" if i in [1, 2, 3, 4] else "Developing",
        "role": "Setter (S)" if i in [1, 2] else ("Outside Hitter (OH)" if i in [3, 4] else "Universal / Utility"),
        "buddy": f"Player {i+6}" if i <= 5 else f"Player {i-5}"
    } for i in range(1, 12)
}

def load_data(file_path, default_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f: return json.load(f)
        except Exception: return default_data
    return default_data

def save_data(file_path, data):
    with open(file_path, "w") as f: json.dump(data, f, indent=4)

def auto_balance_buddies(roster_dict):
    anchors_core, developing = [], []
    for p_name, p_data in roster_dict.items():
        t = p_data.get("tier", "Developing")
        if "Floating" in t or "Floating" in p_data.get("buddy", ""): continue
        if t in ["Anchor", "Playmaker", "Server Specialist", "Defensive Specialist", "Anchor / Floating Rotator"]: anchors_core.append(p_name)
        else: developing.append(p_name)
    pairs_count = min(len(anchors_core), len(developing))
    for i in range(pairs_count):
        anc, dev = anchors_core[i], developing[i]
        roster_dict[anc]["buddy"] = dev
        roster_dict[dev]["buddy"] = anc
    return roster_dict

if "passwords" not in st.session_state: st.session_state["passwords"] = load_data(PASSWORDS_FILE, {"Sample Team Workspace": "1234"})
if "team_rosters" not in st.session_state: st.session_state["team_rosters"] = load_data(ROSTER_FILE, {"Sample Team Workspace": DEFAULT_ROSTER})
if "matches" not in st.session_state: st.session_state["matches"] = load_data(MATCHES_FILE, {})

st.title("🏐 CBRC Universal Volleyball Lineup & Stat Hub")

col_top1, col_top2 = st.columns([1, 2])
with col_top1:
    team_options = list(st.session_state["team_rosters"].keys()) + ["➕ Register New Team Workspace"]
    selected_team = st.selectbox("Select Active Team Workspace:", team_options)

    if selected_team == "➕ Register New Team Workspace":
        with st.form("new_team_form"):
            new_t_name = st.text_input("New Team Name:")
            new_t_pin = st.text_input("Set Team PIN / Password:", type="password")
            if st.form_submit_button("🔒 Register Team Workspace"):
                if new_t_name and new_t_pin:
                    st.session_state["team_rosters"][new_t_name] = DEFAULT_ROSTER
                    st.session_state["passwords"][new_t_name] = new_t_pin
                    save_data(ROSTER_FILE, st.session_state["team_rosters"])
                    save_data(PASSWORDS_FILE, st.session_state["passwords"])
                    st.toast(f"Registered {new_t_name}!", icon="✅")
                    st.rerun()
    else:
        st.session_state["active_team"] = selected_team
        team_pin = st.text_input(f"🔒 Enter PIN for {selected_team}:", type="password")
        if team_pin != st.session_state["passwords"].get(selected_team, ""):
            st.warning("🔒 Please enter the correct Team PIN to unlock your lineup workspace.")
            st.stop()

active_team = st.session_state["active_team"]
current_team_dict = st.session_state["team_rosters"][active_team]
active_team_roster = list(current_team_dict.keys())

with col_top2:
    match_list = [k for k, v in st.session_state["matches"].items() if v.get("team") == active_team] + ["➕ Create New Game"]
    selected_match_key = st.selectbox("Select Active Game / Match Archive:", match_list)

tab_lineup, tab_court, tab_stats, tab_roles, tab_history, tab_rules = st.tabs([
    "📋 Lineup Generator", "🏐 Court Diagram", "📊 Live Serve Tracker",
    "👥 Roster & Roles", "📈 Season History", "⚙️ League Rules"
])

with tab_lineup:
    st.header(f"📋 Lineup Generator - {active_team}")
    if selected_match_key == "➕ Create New Game" or not selected_match_key:
        c1, c2, c3 = st.columns(3)
        with c1: game_num = st.text_input("Game Name", "Game 1")
        with c2: opp_name = st.text_input("Opponent", "Opponent")
        with c3: game_date = st.date_input("Date", datetime.date.today())
       
        st.markdown("### 🚫 Attendance & Absence Tracker")
        absent_players = st.multiselect("Mark Players Absent / Out Today:", active_team_roster, default=[])
        active_list = [p for p in active_team_roster if p not in absent_players]
        rot_style = st.selectbox("Rotation System:", ["Buddy System (Equal Play / Rec)", "Fixed Core Positions"])
       
        if st.button("🚀 Generate & Save Match"):
            p_list = active_list.copy()
            st.session_state["matches"][f"{game_num} vs {opp_name} ({game_date.strftime('%m/%d/%Y')})"] = {
                "team": active_team, "date": str(game_date), "opponent": opp_name, "mode": rot_style, "active_players": active_list,
                "lineup": {
                    "Set 1": {"Starters": p_list[:6], "Subs": p_list[6:]},
                    "Set 2": {"Starters": p_list[6:] + p_list[:6-len(p_list[6:])], "Subs": p_list[:6]},
                    "Set 3": {"Starters": p_list[:6], "Subs": p_list[6:]}
                },
                "stats": {p: {"Attempts": 0, "Makes": 0, "Aces": 0, "Points_Won": 0} for p in active_list}
            }
            save_data(MATCHES_FILE, st.session_state["matches"])
            st.toast("Saved match!", icon="💾")
            st.rerun()
    else:
        current_data = st.session_state["matches"][selected_match_key]
        st.subheader(f"Active Match: {selected_match_key}")
       
        with st.expander("🖨️ Display Bench Clipboard Sheet (Print / Screenshot)", expanded=False):
            st.markdown("## 📋 Match Bench Lineup Sheet")
            col_b1, col_b2, col_b3 = st.columns(3)
            for set_n, col_b in zip(["Set 1", "Set 2", "Set 3"], [col_b1, col_b2, col_b3]):
                with col_b:
                    st.markdown(f"### **{set_n}**")
                    st.markdown("**Starters:**")
                    for i, p in enumerate(current_data["lineup"][set_n]["Starters"], 1):
                        st.write(f"{i}. **{p}** ({current_team_dict.get(p, {}).get('role', 'Utility')})")
                    st.markdown("**Bench Subs:**")
                    for p in current_data["lineup"][set_n]["Subs"]:
                        st.write(f"🔄 {p}")

        st.markdown("---")
        s1, s2, s3 = st.tabs(["Set 1", "Set 2", "Set 3"])
        for set_num, set_tab in zip(["Set 1", "Set 2", "Set 3"], [s1, s2, s3]):
            with set_tab:
                c_st, c_su = st.columns(2)
                with c_st:
                    st.markdown("### 🏐 Starting 6")
                    for idx in range(6):
                        curr_p = current_data["lineup"][set_num]["Starters"][idx] if idx < len(current_data["lineup"][set_num]["Starters"]) else active_team_roster[0]
                        st.selectbox(f"Pos {idx+1}:", active_team_roster, index=active_team_roster.index(curr_p) if curr_p in active_team_roster else 0, key=f"{selected_match_key}_{set_num}_st_{idx}")
                with c_su:
                    st.markdown("### 🔄 Bench Subs")
                    for idx in range(6):
                        curr_s = current_data["lineup"][set_num]["Subs"][idx] if idx < len(current_data["lineup"][set_num]["Subs"]) else "Open"
                        st.selectbox(f"Sub {idx+1}:", active_team_roster + ["Open"], key=f"{selected_match_key}_{set_num}_su_{idx}")

# --- REST OF TABS ---
with tab_court:
    st.header("🏐 2D Court Formation")

with tab_stats:
    st.header("📊 Live Serve & Point Tracker")

with tab_roles:
    st.header("👥 Roster Settings & Auto-Balancer")

with tab_history:
    st.header("📈 Season Aggregates")

with tab_rules:
    st.header("⚙️ CBRC League Rules")
