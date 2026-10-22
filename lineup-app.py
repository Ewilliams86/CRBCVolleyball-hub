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

# --- MASTER DIRECTOR ADMIN PIN ---
DIRECTOR_MASTER_PIN = "CBRCADMIN2026"

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
                    st.session_state["team_rosters"][new_t_name] = {}
                    st.session_state["passwords"][new_t_name] = new_t_pin
                    save_data(ROSTER_FILE, st.session_state["team_rosters"])
                    save_data(PASSWORDS_FILE, st.session_state["passwords"])
                    st.toast(f"Registered {new_t_name}!", icon="✅")
                    st.rerun()
    else:
        st.session_state["active_team"] = selected_team
        team_pin = st.text_input(f"🔒 Enter PIN for {selected_team} (or Master PIN):", type="password")
       
        is_director = (team_pin == DIRECTOR_MASTER_PIN)
        correct_team_pin = st.session_state["passwords"].get(selected_team, "")
       
        if not is_director and team_pin != correct_team_pin:
            st.warning("🔒 Please enter the correct Team PIN or Master Director Key to unlock.")
            st.stop()
           
        if is_director:
            st.success("👑 Master Director Key Accepted - Admin Mode Active")

active_team = st.session_state.get("active_team", "Sample Team Workspace")
current_team_dict = st.session_state["team_rosters"].get(active_team, {})
active_team_roster = list(dict.fromkeys(current_team_dict.keys()))

with col_top2:
    match_list = [k for k, v in st.session_state["matches"].items() if v.get("team") == active_team] + ["➕ Create New Game"]
    selected_match_key = st.selectbox("Select Active Game / Match Archive:", match_list)

if 'team_pin' in locals() and team_pin == DIRECTOR_MASTER_PIN:
    with st.expander("👑 League Director Master Portal (Password Recovery & Overview)", expanded=True):
        st.markdown("### 🔑 Registered Team Passwords Master Table")
        pwd_rows = [{"Team Workspace": t, "Assigned PIN": p, "Registered Players": len(st.session_state["team_rosters"].get(t, {}))} for t, p in st.session_state["passwords"].items()]
        st.dataframe(pd.DataFrame(pwd_rows), use_container_width=True)

st.markdown("---")

# HERE WAS THE FIX: 'tab_ai' IS NOW PROPERLY DEFINED IN THIS LIST!
tab_lineup, tab_court, tab_stats, tab_roles, tab_history, tab_rules, tab_ai = st.tabs([
    "📋 Lineup Generator", "🏐 Court Diagram", "📊 Live Serve Tracker",
    "👥 Roster & Roles", "📈 Season History", "⚙️ League Rules", "🤖 AI Assistant"
])

# --- TAB 1: LINEUP GENERATOR ---
with tab_lineup:
    st.header(f"📋 Lineup Generator - {active_team}")
   
    st.markdown("### 🚫 Pre-Game Attendance & Absence Tracker")
    absent_selected = st.multiselect("Mark Players Absent / Out Today:", active_team_roster, key="absent_tracker_hub")
   
    available_roster = [p for p in active_team_roster if p not in absent_selected]
    st.markdown("---")
   
    if selected_match_key == "➕ Create New Game" or not selected_match_key:
        c1, c2, c3 = st.columns(3)
        with c1: game_num = st.text_input("Game Name", "Game 1")
        with c2: opp_name = st.text_input("Opponent", "Opponent")
        with c3: game_date = st.date_input("Date", datetime.date.today())
       
        rot_style = st.selectbox("Rotation System:", ["Buddy System (Equal Play / Rec)", "Fixed Core Positions"])
       
        if st.button("🚀 Generate & Save Match"):
            if not available_roster:
                st.error("Please add players to your roster in '👥 Roster & Roles' first!")
            else:
                p_list = available_roster.copy()
                while len(p_list) < 6:
                    p_list.append(f"Open Position {len(p_list)+1}")
               
                s1_starters = p_list[:6]
                s1_subs = p_list[6:] if len(p_list) > 6 else ["Open"]
                s2_starters = (p_list[6:] + p_list[:6])[:6]
                s2_subs = [p for p in p_list if p not in s2_starters] or ["Open"]
                s3_starters = p_list[:6]
                s3_subs = p_list[6:] if len(p_list) > 6 else ["Open"]
               
                new_title = f"{game_num} vs {opp_name} ({game_date.strftime('%m/%d/%Y')})"
                st.session_state["matches"][new_title] = {
                    "team": active_team, "date": str(game_date), "opponent": opp_name, "mode": rot_style, "active_players": available_roster,
                    "lineup": {
                        "Set 1": {"Starters": s1_starters, "Subs": s1_subs},
                        "Set 2": {"Starters": s2_starters, "Subs": s2_subs},
                        "Set 3": {"Starters": s3_starters, "Subs": s3_subs}
                    },
                    "stats": {p: {"Attempts": 0, "Makes": 0, "Aces": 0, "Points_Won": 0} for p in available_roster}
                }
                save_data(MATCHES_FILE, st.session_state["matches"])
                st.toast("Generated lineup with 6 unique positions!", icon="🚀")
                st.rerun()
    else:
        current_data = st.session_state["matches"][selected_match_key]
        st.subheader(f"Active Match: {selected_match_key}")
       
        with st.expander("🖨️ Display Bench Clipboard Sheet (Print / Screenshot)", expanded=True):
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
                dropdown_options = available_roster.copy()
                if not dropdown_options:
                    dropdown_options = [f"Open Position {i}" for i in range(1, 7)]
                   
                with c_st:
                    st.markdown("### 🏐 Starting 6")
                    curr_starters = current_data["lineup"][set_num]["Starters"]
                    while len(curr_starters) < 6:
                        curr_starters.append(dropdown_options[len(curr_starters) % len(dropdown_options)])
                    for idx in range(6):
                        curr_p = curr_starters[idx]
                        p_idx = dropdown_options.index(curr_p) if curr_p in dropdown_options else 0
                        sel_p = st.selectbox(f"Pos {idx+1}:", dropdown_options, index=p_idx, key=f"{selected_match_key}_{set_num}_st_{idx}")
                        curr_starters[idx] = sel_p
                       
                with c_su:
                    st.markdown("### 🔄 Bench Subs")
                    sub_opts = dropdown_options + ["Open"]
                    curr_subs = current_data["lineup"][set_num]["Subs"]
                    if not curr_subs: curr_subs = ["Open"]
                    for idx in range(len(curr_subs)):
                        curr_s = curr_subs[idx]
                        s_idx = sub_opts.index(curr_s) if curr_s in sub_opts else 0
                        sel_s = st.selectbox(f"Sub {idx+1}:", sub_opts, index=s_idx, key=f"{selected_match_key}_{set_num}_su_{idx}")
                        curr_subs[idx] = sel_s

        if st.button("💾 Permanently Save Lineup Changes"):
            save_data(MATCHES_FILE, st.session_state["matches"])
            st.toast("Saved lineup edits!", icon="💾")

# --- TAB 2: COURT DIAGRAM ---
with tab_court:
    st.header("🏐 2D Court Formation")
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
        if p_list:
            col_c, col_v = st.columns([1, 2])
            with col_c:
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

            with col_v:
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
                st.dataframe(pd.DataFrame(stats_rows), use_container_width=True)

# --- TAB 4: ROSTER & ROLES ---
with tab_roles:
    st.header(f"👥 Roster Settings & Roles - {active_team}")
    tier_opts = ["Anchor", "Playmaker", "Developing", "Server Specialist", "Defensive Specialist", "Anchor / Floating Rotator"]
    role_opts = ["Setter (S)", "Libero / DS (L)", "Outside Hitter (OH)", "Middle Blocker (MB)", "Right Side (OPP)", "Defensive Specialist (DS)", "Universal / Utility"]
   
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Current Workspace Roster")
        if current_team_dict:
            st.dataframe(pd.DataFrame([{"Player": k, "Tier": v.get("tier"), "Role": v.get("role"), "Buddy": v.get("buddy")} for k, v in current_team_dict.items()]), use_container_width=True)
            if st.button("⚡ Auto-Balance Buddy Pairs Now"):
                st.session_state["team_rosters"][active_team] = auto_balance_buddies(current_team_dict)
                save_data(ROSTER_FILE, st.session_state["team_rosters"])
                st.toast("Auto-balanced buddies!", icon="⚡")
                st.rerun()
        else:
            st.info("No players added yet! Use the form on the right to add your team roster.")

    with c2:
        st.subheader("➕ Add New Player")
        with st.form("add_new_player_form"):
            add_p_name = st.text_input("Player Name:")
            add_p_tier = st.selectbox("Assign Skill Tier:", tier_opts)
            add_p_role = st.selectbox("Assign Position Role:", role_opts)
           
            if st.form_submit_button("➕ Add Player to Team"):
                if add_p_name:
                    st.session_state["team_rosters"][active_team][add_p_name] = {"tier": add_p_tier, "role": add_p_role, "buddy": "Open"}
                    save_data(ROSTER_FILE, st.session_state["team_rosters"])
                    st.toast(f"Added {add_p_name} to roster!", icon="✅")
                    st.rerun()

        if active_team_roster:
            st.markdown("---")
            st.subheader("✏️ Edit / Rename Existing Player")
            edit_p = st.selectbox("Select Player:", active_team_roster, key="edit_public_p")
            with st.form("edit_player_form"):
                u_name = st.text_input("Rename Player:", value=edit_p)
                u_tier = st.selectbox("Tier:", tier_opts, index=tier_opts.index(current_team_dict[edit_p].get("tier", "Developing")) if current_team_dict[edit_p].get("tier") in tier_opts else 0)
                u_role = st.selectbox("Role:", role_opts, index=role_opts.index(current_team_dict[edit_p].get("role", "Universal / Utility")) if current_team_dict[edit_p].get("role") in role_opts else 0)
                if st.form_submit_button("💾 Save Edits"):
                    st.session_state["team_rosters"][active_team][u_name] = {"tier": u_tier, "role": u_role, "buddy": "Open"}
                    if u_name != edit_p: del st.session_state["team_rosters"][active_team][edit_p]
                    save_data(ROSTER_FILE, st.session_state["team_rosters"])
                    st.toast(f"Updated {u_name}!", icon="💾")
                    st.rerun()

# --- TAB 5: SEASON HISTORY ---
with tab_history:
    st.header(f"📈 Season Aggregates - {active_team}")

# --- TAB 6: LEAGUE RULES ---
with tab_rules:
    st.header("⚙️ CBRC League Rules & Settings Engine")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.subheader("Substitution Limits & Formats")
        st.slider("Max Subs Per Stoppage", 1, 6, 3)
        st.number_input("Mandatory Sub Credits Per Match", 1, 10, 4)
        st.selectbox("Match Format", ["3 Fixed Sets (CBRC Standard)", "Best 2 out of 3", "Best 3 out of 5"])
    with col_r2:
        st.subheader("Participation Guidelines")
        st.selectbox("Set Starting Requirement", ["Must start Set 1 or Set 2 (CBRC)", "Must start at least 1 set", "Open / Coach Choice"])
        st.checkbox("Enforce Set 3 Participation for All Active Players", value=True)
        st.checkbox("Enable Libero / Position Tracking", value=True)

# --- TAB 7: AI ASSISTANT ---
with tab_ai:
    st.header("🤖 AI Rotation & Coaching Assistant")
    st.info("💡 Type any rotation question, rule adjustment, or serve opportunity tweak below!")
   
    user_prompt = st.text_area(
        "Enter your coaching adjustment or question:",
        placeholder="e.g., A player needs more serve time in Set 2. Adjust our starters while keeping buddy rules compliant."
    )
   
    if st.button("✨ Ask AI Assistant"):
        st.success("AI Helper Tab Ready! (Configure your GEMINI_API_KEY in Streamlit Secrets to enable live response generation).")

 
