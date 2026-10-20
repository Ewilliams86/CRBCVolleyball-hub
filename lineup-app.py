import streamlit as st
import pandas as pd
import datetime
import json
import os

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Volley Llamas - Lineup & Match Hub",
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
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .stMarkdown h3 {
        color: #38BDF8 !important;
        font-size: 1.1rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 600;
        color: #38BDF8 !important;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px 16px;
    }
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        font-weight: 600;
        color: #94A3B8;
    }
    button[aria-selected="true"] {
        color: #38BDF8 !important;
        border-bottom-color: #38BDF8 !important;
    }
    .stButton>button {
        background-color: #0284C7;
        color: #FFFFFF;
        font-weight: 600;
        border-radius: 6px;
        border: none;
        padding: 6px 14px;
    }
    </style>
""", unsafe_allow_html=True)

# --- PERMANENT FILE STORAGE PATHS ---
ROSTER_FILE = "roster_data.json"
MATCHES_FILE = "match_archive.json"

DEFAULT_ROSTER = {
    "Quinn": {"tier": "Anchor", "role": "Setter (S)", "buddy": "Claire"},
    "Claire": {"tier": "Developing", "role": "Outside Hitter (OH)", "buddy": "Quinn"},
    "Heidi": {"tier": "Anchor", "role": "Outside Hitter (OH)", "buddy": "Lola"},
    "Lola": {"tier": "Developing", "role": "Defensive Specialist (DS)", "buddy": "Heidi"},
    "Alivia": {"tier": "Anchor", "role": "Setter (S)", "buddy": "Khloe"},
    "Khloe": {"tier": "Developing", "role": "Right Side (OPP)", "buddy": "Alivia"},
    "Ellie": {"tier": "Playmaker", "role": "Middle Blocker (MB)", "buddy": "Brinley"},
    "Brinley": {"tier": "Developing", "role": "Outside Hitter (OH)", "buddy": "Ellie"},
    "Lillian": {"tier": "Playmaker", "role": "Libero / DS (L)", "buddy": "Emmalani"},
    "Emmalani": {"tier": "Playmaker", "role": "Middle Blocker (MB)", "buddy": "Lillian"},
    "Ella": {"tier": "Anchor / Floating Rotator", "role": "Universal / Utility", "buddy": "None (Floating)"}
}

DEFAULT_MATCHES = {}

# --- PERSISTENCE HELPERS ---
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

# --- INITIALIZE SESSION STATE ---
if "roster" not in st.session_state:
    st.session_state["roster"] = load_data(ROSTER_FILE, DEFAULT_ROSTER)

if "matches" not in st.session_state:
    st.session_state["matches"] = load_data(MATCHES_FILE, DEFAULT_MATCHES)

active_team = "Volley Llamas (CBRC Team 4)"
active_team_roster = list(st.session_state["roster"].keys())

# --- GLOBAL TOP BAR ---
st.title("🏐 CBRC Volley Llamas - Lineup & Stat Hub")

col_top1, col_top2 = st.columns([1, 2])
with col_top1:
    st.subheader(f"Team: {active_team}")

with col_top2:
    match_list = list(st.session_state["matches"].keys()) + ["➕ Create New Game"]
    selected_match_key = st.selectbox("Select Active Game / Archive:", match_list)

# --- NAVIGATION TABS ---
tab_lineup, tab_court, tab_stats, tab_roles, tab_history, tab_rules = st.tabs([
    "📋 Lineup Generator",
    "🏐 Court Diagram",
    "📊 Live Serve Tracker",
    "👥 Roster & Roles",
    "📈 Season History",
    "⚙️ League Rules"
])

# --- TAB 1: LINEUP GENERATOR (WITH ABSENCE TOGGLE & BENCH SHEET) ---
with tab_lineup:
    st.header(f"📋 Lineup Generator - {active_team}")
   
    if selected_match_key == "➕ Create New Game" or not selected_match_key:
        c1, c2, c3 = st.columns(3)
        with c1: game_num = st.text_input("Game Name", "Game 2")
        with c2: opp_name = st.text_input("Opponent", "Blazers")
        with c3: game_date = st.date_input("Date", datetime.date.today())
       
        # FEATURE 5: ABSENCE TOGGLE
        st.markdown("### 🚫 Attendance & Absence Tracker")
        absent_players = st.multiselect("Mark Players Absent / Out Today:", active_team_roster, default=[])
        active_list = [p for p in active_team_roster if p not in absent_players]
       
        rot_style = st.selectbox("Select Rotation System:", ["Buddy System (Equal Play / Rec)", "Fixed Core Positions"])
       
        if st.button("🚀 Generate & Save Match"):
            p_list = active_list.copy()
            st.session_state["matches"][f"{game_num} vs {opp_name} ({game_date.strftime('%m/%d/%Y')})"] = {
                "team": active_team,
                "date": str(game_date),
                "opponent": opp_name,
                "mode": rot_style,
                "active_players": active_list,
                "lineup": {
                    "Set 1": {"Starters": p_list[:6], "Subs": p_list[6:] + ["Open"] * max(0, 12 - len(p_list))},
                    "Set 2": {"Starters": (p_list[6:] + p_list[:6])[:6], "Subs": (p_list[:6] + ["Open"])[:6]},
                    "Set 3": {"Starters": p_list[:6], "Subs": p_list[6:] + ["Open"] * max(0, 12 - len(p_list))}
                },
                "stats": {p: {"Attempts": 0, "Makes": 0, "Aces": 0, "Points_Won": 0} for p in active_list}
            }
            save_data(MATCHES_FILE, st.session_state["matches"])
            st.toast(f"Saved {game_num} vs {opp_name}!", icon="💾")
            st.rerun()
           
    else:
        current_data = st.session_state["matches"][selected_match_key]
        st.subheader(f"Active Match: {selected_match_key}")
       
        # FEATURE 1: PRINTABLE BENCH CLIPBOARD SUMMARY VIEW
        with st.expander("🖨️ Display Bench Clipboard Sheet (Print / Screenshot)", expanded=False):
            st.markdown("## 📋 Match Bench Lineup Sheet")
            col_b1, col_b2, col_b3 = st.columns(3)
            for set_n, col_b in zip(["Set 1", "Set 2", "Set 3"], [col_b1, col_b2, col_b3]):
                with col_b:
                    st.markdown(f"### **{set_n}**")
                    st.markdown("**Starters:**")
                    for i, p in enumerate(current_data["lineup"][set_n]["Starters"], 1):
                        st.write(f"{i}. **{p}** ({st.session_state['roster'].get(p, {}).get('role', 'Utility')})")
                    st.markdown("**Bench Subs:**")
                    for p in current_data["lineup"][set_n]["Subs"]:
                        st.write(f"🔄 {p}")
                       
        st.markdown("---")
        s1, s2, s3 = st.tabs(["Set 1 Lineup", "Set 2 Lineup", "Set 3 Lineup"])
        for set_num, set_tab in zip(["Set 1", "Set 2", "Set 3"], [s1, s2, s3]):
            with set_tab:
                col_st, col_su = st.columns(2)
                with col_st:
                    st.markdown("### 🏐 Starting 6")
                    for idx in range(6):
                        curr_p = current_data["lineup"][set_num]["Starters"][idx] if idx < len(current_data["lineup"][set_num]["Starters"]) else active_team_roster[0]
                        st.selectbox(f"Pos {idx+1}:", active_team_roster, index=active_team_roster.index(curr_p) if curr_p in active_team_roster else 0, key=f"{selected_match_key}_{set_num}_st_{idx}")
                with col_su:
                    st.markdown("### 🔄 Bench Subs")
                    for idx in range(6):
                        curr_s = current_data["lineup"][set_num]["Subs"][idx] if idx < len(current_data["lineup"][set_num]["Subs"]) else "Open"
                        st.selectbox(f"Sub {idx+1}:", active_team_roster + ["Open"], key=f"{selected_match_key}_{set_num}_su_{idx}")

# --- TAB 2: COURT DIAGRAM ---
with tab_court:
    st.header("🏐 Visual Court Diagram")
    if selected_match_key != "➕ Create New Game" and selected_match_key:
        current_data = st.session_state["matches"][selected_match_key]
        set_choice = st.radio("Display Set:", ["Set 1", "Set 2", "Set 3"], horizontal=True)
        strs = current_data["lineup"][set_choice]["Starters"]
       
        st.markdown("--- **NET** ---")
        fr1, fr2, fr3 = st.columns(3)
        with fr1: st.metric("Pos 4 (Front Left)", strs[3] if len(strs)>3 else "Open")
        with fr2: st.metric("Pos 3 (Front Center)", strs[2] if len(strs)>2 else "Open")
        with fr3: st.metric("Pos 2 (Front Right)", strs[1] if len(strs)>1 else "Open")
       
        st.markdown("--- 3-Meter Attack Line ---")
        br1, br2, br3 = st.columns(3)
        with br1: st.metric("Pos 5 (Back Left)", strs[4] if len(strs)>4 else "Open")
        with br2: st.metric("Pos 6 (Back Center)", strs[5] if len(strs)>5 else "Open")
        with br3: st.metric("Pos 1 (Server)", strs[0] if len(strs)>0 else "Open")

# --- TAB 3: LIVE SERVE TRACKER ---
with tab_stats:
    st.header("📊 Live Serve & Point Tracker")
    if selected_match_key != "➕ Create New Game" and selected_match_key:
        active_match = st.session_state["matches"][selected_match_key]
        p_list = active_match["active_players"]
       
        col_ctrl, col_view = st.columns([1, 2])
        with col_ctrl:
            server = st.selectbox("Select Current Server:", p_list)
            b1, b2 = st.columns(2)
            with b1:
                if st.button("✅ Serve IN"):
                    active_match["stats"][server]["Attempts"] += 1
                    active_match["stats"][server]["Makes"] += 1
                    save_data(MATCHES_FILE, st.session_state["matches"])
                    st.toast(f"Logged Serve IN for {server}", icon="✅")
                if st.button("🔥 ACE!"):
                    active_match["stats"][server]["Attempts"] += 1
                    active_match["stats"][server]["Makes"] += 1
                    active_match["stats"][server]["Aces"] += 1
                    active_match["stats"][server]["Points_Won"] += 1
                    save_data(MATCHES_FILE, st.session_state["matches"])
                    st.toast(f"🔥 ACE logged for {server}!", icon="🏐")
            with b2:
                if st.button("❌ Serve Out"):
                    active_match["stats"][server]["Attempts"] += 1
                    save_data(MATCHES_FILE, st.session_state["matches"])
                    st.toast(f"Logged Serve Out for {server}", icon="❌")
                if st.button("🏆 Point Scored"):
                    active_match["stats"][server]["Points_Won"] += 1
                    save_data(MATCHES_FILE, st.session_state["matches"])
                    st.toast(f"Point Scored on {server}'s serve!", icon="🏆")

        with col_view:
            st.subheader("Match Box Score")
            stats_rows = []
            for p_name in p_list:
                p_stat = active_match["stats"].get(p_name, {"Attempts": 0, "Makes": 0, "Aces": 0, "Points_Won": 0})
                att = p_stat["Attempts"]
                mks = p_stat["Makes"]
                pct = (mks / att * 100) if att > 0 else 0.0
                stats_rows.append({
                    "Player": p_name, "Attempts": att, "Makes": mks,
                    "Serve %": f"{pct:.1f}%", "Aces": p_stat["Aces"], "Points Scored": p_stat["Points_Won"]
                })
            df_m = pd.DataFrame(stats_rows)
            st.dataframe(df_m, use_container_width=True)

# --- TAB 4: ROSTER & ROLES ---
with tab_roles:
    st.header(f"👥 Roster & Position Settings - {active_team}")
    tier_options = ["Anchor", "Playmaker", "Developing", "Server Specialist", "Defensive Specialist", "Anchor / Floating Rotator"]
    role_options = ["Setter (S)", "Libero / DS (L)", "Outside Hitter (OH)", "Middle Blocker (MB)", "Right Side (OPP)", "Defensive Specialist (DS)", "Universal / Utility"]
    buddy_options = active_team_roster + ["None (Floating)", "Open / Unassigned"]
   
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Current Permanent Roster")
        role_rows = []
        for p_name, p_data in st.session_state["roster"].items():
            role_rows.append({
                "Player": p_name, "Skill Tier": p_data.get("tier", "Developing"),
                "Court Position": p_data.get("role", "Universal / Utility"), "Buddy Partner": p_data.get("buddy", "Open")
            })
        st.dataframe(pd.DataFrame(role_rows), use_container_width=True)
        if st.button("⚡ Auto-Balance Buddy Pairs Now"):
            st.session_state["roster"] = auto_balance_buddies(st.session_state["roster"])
            save_data(ROSTER_FILE, st.session_state["roster"])
            st.toast("⚡ Auto-balanced and saved Buddy Pairs!", icon="⚡")
            st.rerun()

    with c2:
        edit_p = st.selectbox("Select Player to Update:", active_team_roster, key="edit_p_perm")
        with st.form(key="perm_player_form"):
            curr_tier = st.session_state["roster"][edit_p].get("tier", "Developing")
            curr_role = st.session_state["roster"][edit_p].get("role", "Universal / Utility")
            curr_buddy = st.session_state["roster"][edit_p].get("buddy", "Open")
           
            new_t = st.selectbox("Assign Skill Tier:", tier_options, index=tier_options.index(curr_tier) if curr_tier in tier_options else 0)
            new_r = st.selectbox("Assign Position Role:", role_options, index=role_options.index(curr_role) if curr_role in role_options else 0)
            new_b = st.selectbox("Assign Buddy Partner:", buddy_options, index=buddy_options.index(curr_buddy) if curr_buddy in buddy_options else 0)
           
            if st.form_submit_button("💾 Save Player Profile Changes Permanently"):
                st.session_state["roster"][edit_p] = {"tier": new_t, "role": new_r, "buddy": new_b}
                save_data(ROSTER_FILE, st.session_state["roster"])
                st.toast(f"💾 Saved {edit_p}!", icon="✅")
                st.rerun()

# --- TAB 5 & TAB 6 ---
with tab_history:
    st.header(f"📈 Season History - {active_team}")

with tab_rules:
    st.header("⚙️ CBRC League Rules & Settings")
