import streamlit as st
import pandas as pd

# ==========================================
# 🔐 SYSTEM CONFIGURATION & PASSWORD
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Robotics Team Login")
    password_input = st.text_input("Enter Shared Team Password:", type="password")
    if st.button("Unlock Strategy Dashboard"):
        if password_input == st.secrets["TEAM_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect team password. Try again!")
    st.stop()

# ==========================================
# ⚙️ DATA ENGINE CONFIGURATION
# ==========================================
USE_REAL_CSV = False
CSV_FILE_NAME = "team_manager_data.csv"

@st.cache_data
def load_strategic_database():
    if USE_REAL_CSV:
        try: return pd.read_csv(CSV_FILE_NAME)
        except FileNotFoundError: st.error("CSV file not found. Running template data.")

    # Sandbox data including a new Weight factor (max FRC limit is typically 125 lbs)
    data_list = []
    data_list.append({"team_number": 118, "team_name": "Everybot Template", "base_cycle_time": 12.0, "points_per_cycle": 3.0, "reliability": 0.95, "defense_penalty": 3.5, "weight": 120.0})
    data_list.append({"team_number": 254, "team_name": "Elite Cycler Alpha", "base_cycle_time": 7.5, "points_per_cycle": 4.0, "reliability": 0.98, "defense_penalty": 2.0, "weight": 125.0})
    data_list.append({"team_number": 1678, "team_name": "Elite Cycler Beta", "base_cycle_time": 8.0, "points_per_cycle": 4.0, "reliability": 0.96, "defense_penalty": 2.5, "weight": 110.0})
    data_list.append({"team_number": 9999, "team_name": "Fragile Prototype", "base_cycle_time": 15.0, "points_per_cycle": 3.0, "reliability": 0.60, "defense_penalty": 4.0, "weight": 95.0})
    return pd.DataFrame(data_list)

df = load_strategic_database()
available_teams = sorted(df['team_number'].tolist())

# ==========================================
# 🖥️ USER INTERFACE DESIGN
# ==========================================
st.sidebar.markdown(f"### 👤 Strategy Department")
coder_name = st.sidebar.text_input("User Initials/Name:", value="Anonymous")
st.sidebar.divider()

with st.sidebar:
    st.header("🔍 Team Profile Lookup")
    selected_team = st.selectbox("Choose Team Number:", available_teams)
    team_data = df[df['team_number'] == selected_team].iloc[0]
    st.markdown(f"### **Team {team_data['team_number']}**\n*{team_data['team_name']}*")
    st.divider()
    st.metric("🏎️ Undefended Cycle Speed", f"{team_data['base_cycle_time']}s")
    st.metric("⚖️ Robot Weight", f"{team_data['weight']} lbs")
    st.metric("💯 Points Per Cycle", f"{team_data['points_per_cycle']} pts")
    st.metric("🔋 System Reliability", f"{int(team_data['reliability'] * 100)}%")

st.title("🤖 FRC Strategic Design Matrix & Simulator")
st.markdown("This engine accounts for **Weight Dynamics**. Heavier defenders inflict structural loop penalties on lighter targets.")

st.subheader("⚔️ Live 3v3 Physics-Based Matchup")
c_red, c_blue = st.columns(2)

# --- 🔴 RED ALLIANCE UI ---
with c_red:
    st.error("🔴 Red Alliance Configuration")
    r1 = st.selectbox("Red 1", available_teams, index=0)
    r2 = st.selectbox("Red 2", available_teams, index=1)
    r3 = st.selectbox("Red 3", available_teams, index=2)
    
    st.markdown("##### 🛡️ Red Defense Assignment")
    red_defender = st.selectbox("Which Red robot plays defense?", ["None", "Red 1", "Red 2", "Red 3"])
    red_def_time = st.slider("Defense Duration (Seconds):", 0, 135, 0, key="red_slider")

# --- 🔵 BLUE ALLIANCE UI ---
with c_blue:
    st.info("🔵 Blue Alliance Configuration")
    b1 = st.selectbox("Blue 1", available_teams, index=2)
    b2 = st.selectbox("Blue 2", available_teams, index=1)
    b3 = st.selectbox("Blue 3", available_teams, index=3)
    
    st.markdown("##### 🛡️ Blue Defense Assignment")
    blue_defender = st.selectbox("Which Blue robot plays defense?", ["None", "Blue 1", "Blue 2", "Blue 3"])
    blue_def_time = st.slider("Defense Duration (Seconds):", 0, 135, 0, key="blue_slider")

# ==========================================
# 📊 PHYSICS-BASED MATCH CALCULATION ENGINE
# ==========================================
def calculate_match_points(alliance_teams, defender_selection, def_time, opponent_teams, opponent_defender_selection, opponent_def_time):
    total_alliance_score = 0.0
    
    # 1. Identify the specific defender team ids if active
    our_def_id = None
    if defender_selection != "None":
        slot_idx = int(defender_selection.split()[-1]) - 1
        our_def_id = alliance_teams[slot_idx]
        
    opp_def_id = None
    if opponent_defender_selection != "None" and opponent_def_time > 0:
        opp_slot_idx = int(opponent_defender_selection.split()[-1]) - 1
        opp_def_id = opponent_teams[opp_slot_idx]

    # 2. Process each robot in our alliance
    for index, tid in enumerate(alliance_teams):
        team = df[df['team_number'] == tid].iloc[0]
        
        # Check if this specific robot is busy defending
        is_assigned_defender = (defender_selection != "None" and f"{index+1}" in defender_selection)
        scoring_time_available = (135.0 - def_time) if is_assigned_defender else 135.0
        
        if scoring_time_available > 0:
            defense_drag_per_cycle = 0.0
            
            # If an opponent defender is active, calculate physics-scaled drag on THIS target robot
            if opp_def_id is not None:
                opp_def_row = df[df['team_number'] == opp_def_id].iloc[0]
                
                # Physics/Weight Multiplier: (Defender Weight / Target Weight)
                # If defender is heavier, multiplier > 1 (worse penalty). If lighter, multiplier < 1.
                weight_multiplier = opp_def_row['weight'] / team['weight']
                
                # Base penalty scaled by match presence ratio and structural leverage
                base_opp_penalty = opp_def_row['defense_penalty']
                match_presence_ratio = opponent_def_time / 135.0
                
                defense_drag_per_cycle = match_presence_ratio * base_opp_penalty * weight_multiplier
            
            # Final scoring math
            actual_cycle_time = team['base_cycle_time'] + defense_drag_per_cycle
            cycles_completed = scoring_time_available / actual_cycle_time
            expected_points = (cycles_completed * team['points_per_cycle']) * team['reliability']
            total_alliance_score += expected_points
            
    return round(total_alliance_score, 1)

# --- EXECUTE ENGINE BUTTON ---
st.markdown("---")
if st.button("🚀 Calculate Strategic Match Simulation", use_container_width=True):
    red_teams = [r1, r2, r3]
    blue_teams = [b1, b2, b3]
    
    red_final = calculate_match_points(red_teams, red_defender, red_def_time, blue_teams, blue_defender, blue_def_time)
    blue_final = calculate_match_points(blue_teams, blue_defender, blue_def_time, red_teams, red_defender, red_def_time)
    
    res_r, res_b = st.columns(2)
    res_r.metric("Red Alliance Predicted Output", f"{red_final} Pts")
    res_b.metric("Blue Alliance Predicted Output", f"{blue_final} Pts")
    
    if red_final > blue_final:
        st.success(f"🏆 Red Alliance holds a data advantage of {round(red_final - blue_final, 1)} points!")
    elif blue_final > red_final:
        st.info(f"🏆 Blue Alliance holds a data advantage of {round(blue_final - red_final, 1)} points!")
    else:
        st.warning("Prediction models yield a dead tactical split!")