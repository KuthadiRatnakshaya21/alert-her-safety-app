import streamlit as st
import pandas as pd
import datetime
import os
from gtts import gTTS
from risk_engine import RISK_ZONES, calculate_risk

try:
    import folium
    from streamlit_folium import st_folium
except ImportError:
    st.error("Please ensure folium and streamlit-folium are added to requirements.txt")

st.set_page_config(page_title="ALERT HER", page_icon="🛡️", layout="wide")

# --- INITIALIZE CROWD STORY MEMORY STATE METRIC SYSTEM ---
if "stories" not in st.session_state:
    now_time = datetime.datetime.now()
    st.session_state.stories = [
        {
            "id": 101, "location": "ITO", "issue": "Severe streetlight failure along metro access corridor.",
            "quote": "Extremely dark stretch near the main entry gate—please avoid walking solo.",
            "timestamp": now_time - datetime.timedelta(minutes=10), "avatar": "⚠️", "archived": False
        },
        {
            "id": 102, "location": "Sultanpuri", "issue": "Rowdy assembly flagged near market square corridors.",
            "quote": "Unregulated groups loitering near narrow lanes. Take the bypass highway route.",
            "timestamp": now_time - datetime.timedelta(minutes=45), "avatar": "🚨", "archived": False
        }
    ]

if "contacts" not in st.session_state:
    st.session_state.contacts = [
        {"id": 0, "name": "Mom", "relation": "Mother", "gender": "Female", "script": "Hey beta, where are you? I am waiting outside for you, please call me back as soon as you see this.", "audio_bytes": None},
        {"id": 1, "name": "Dad", "relation": "Father", "gender": "Male", "script": "Beta, have you boarded your ride yet? Share your live location right now.", "audio_bytes": None},
        {"id": 2, "name": "Dr. Sharma", "relation": "Doctor", "gender": "Male", "script": "This is Dr. Sharma's clinic. Your medical reports are ready for collection, please call back tomorrow.", "audio_bytes": None},
        {"id": 3, "name": "Kriti", "relation": "Sister", "gender": "Female", "script": "Hey! I have reached the restaurant already, where are you stuck? Ready to order!", "audio_bytes": None},
        {"id": 4, "name": "Rahul", "relation": "Brother", "gender": "Male", "script": "Listen, I am standing near the metro gate number 2. Walk fast, your train arrived.", "audio_bytes": None}
    ]
if "next_id" not in st.session_state: st.session_state.next_id = 5
if "next_story_id" not in st.session_state: st.session_state.next_story_id = 103
if "active_call" not in st.session_state: st.session_state.active_call = None

# --- GLOBAL STYLES & INLINE REPRODUCED INSTAGRAM REPRODUCTION CSS ---
st.markdown("""
<style>
    .main-title { font-size: 2.6rem; font-weight: 800; color: #e53e3e; margin-bottom: 0px; }
    .tagline { font-size: 1.1rem; color: #4a5568; margin-bottom: 25px; font-style: italic; }
    .risk-badge {
        padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 1.2rem;
        display: inline-block; color: white; text-align: center; margin-bottom: 15px;
    }
    .badge-low { background-color: #2f9e44; }
    .badge-moderate { background-color: #dd8c2b; }
    .badge-high {
        background-color: #e53e3e; box-shadow: 0 0 0 0 rgba(229, 62, 62, 1);
        animation: pulse-red 2s infinite;
    }
    @keyframes pulse-red {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(229, 62, 62, 0.7); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 10px rgba(229, 62, 62, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(229, 62, 62, 0); }
    }
    .disclaimer-style {
        font-size: 0.85rem; color: #718096; text-align: center;
        margin-top: 40px; padding: 15px; border-top: 1px solid #e2e8f0; line-height: 1.4; font-weight: 500;
    }
    .story-bubble {
        border: 3px solid #e53e3e; border-radius: 50%; width: 72px; height: 72px;
        display: flex; align-items: center; justify-content: center; font-size: 2rem;
        background-color: white; margin: 0 auto; cursor: pointer;
        animation: story-glow 1.5s ease-in-out infinite alternate;
    }
    .story-bubble-empty {
        border: 3px dashed #cbd5e0; border-radius: 50%; width: 72px; height: 72px;
        display: flex; align-items: center; justify-content: center; font-size: 2rem;
        background-color: #f7fafc; margin: 0 auto; color: #a0aec0;
    }
    @keyframes story-glow {
        0% { border-color: #e53e3e; box-shadow: 0 0 5px rgba(229,62,62,0.4); }
        100% { border-color: #dd8c2b; box-shadow: 0 0 12px rgba(221,140,43,0.7); }
    }
    .story-container { text-align: center; margin: 10px; font-weight: bold; font-size: 0.85rem; }
    .quote-card {
        background-color: #fffaf0; border-left: 4px solid #dd8c2b; padding: 10px 15px;
        margin-bottom: 12px; border-radius: 0 8px 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .quote-title { font-size: 0.9rem; font-weight: 800; color: #2d3748; margin-bottom: 2px; }
    .quote-body { font-size: 0.85rem; font-style: italic; color: #4a5568; line-height: 1.3; }
    .phone-screen {
        background-color: #1a202c; border: 4px solid #4a5568; border-radius: 24px;
        padding: 40px 20px; text-align: center; color: white; max-width: 320px; margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🛡️ ALERT HER — A Women\'s Safety App</p>', unsafe_allow_html=True)
st.markdown('<p class="tagline">An AI-first safety app that predicts risk before travel, suggests safer decisions, and finds nearby help—preventing emergencies instead of reacting to them.</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📍 Risk Before You Go", "📉 What-If Simulator", "📞 Pretend Call"])

DISCLAIMER_TEXT = "Disclaimer: The safety score and operational risk calculator tools computed by this application are derived strictly from historical crime metrics, geographical reporting trends, and crowd-sourced user inputs. They do not constitute personalized security guarantees or reflect live real-time crime tracking."

# --- FILTER ACTIVE AND NON-EXPIRED STORIES (STAYS FOR 48 HOURS MAXIMUM) ---
current_time_marker = datetime.datetime.now()
active_live_stories = []
archived_profile_stories = []

for s in st.session_state.stories:
    if isinstance(s["timestamp"], str):
        s["timestamp"] = current_time_marker
    time_delta = current_time_marker - s["timestamp"]
    if s.get("archived", False):
        archived_profile_stories.append(s)
    elif time_delta.total_seconds() < (48 * 3600):
        active_live_stories.append(s)
    else:
        s["archived"] = True
        archived_profile_stories.append(s)
# ==============================================================================
# TAB 1: RISK BEFORE YOU GO (PART 1 OF 2)
# ==============================================================================
with tab1:
    st.header("Location Safety Evaluation & Live Incidents")
    
    col_left, col_mid, col_right = st.columns([2, 2, 1.2])
    
    with col_left:
        st.subheader("Configure Travel Vector")
        zone_options = list(RISK_ZONES.keys()) + ["Other (Custom Location)"]
        selected_zone = st.selectbox("Select Target Destination", options=zone_options, key="tab1_zone_select")
        
        custom_name = ""
        if selected_zone == "Other (Custom Location)":
            custom_name = st.text_input("Enter Locality Name", value="", key="tab1_custom_name")
            eval_zone = custom_name if custom_name else "Other"
        else:
            eval_zone = selected_zone
            
        t1_time = st.time_input("Planned Departure Time", value=datetime.datetime.now().time(), key="tab1_time_input")
        t1_wknd = st.checkbox("Traveling on a Weekend?", key="tab1_weekend_chk")
        
        st.markdown("---")
        st.subheader("💬 AI Safety Assistant Chatbot")
        st.caption("Report micro-hazards here. What you submit adds a dynamic alert story and populates the quote wall feed live.")
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["text"])
                
        if chat_input := st.chat_input("State the issue (e.g. 'Poor lighting near metro gate')...", key="tab1_chat_field"):
            st.session_state.chat_history.append({"role": "user", "text": chat_input})
            st.session_state.chat_history.append({"role": "assistant", "text": "Hazard logged across community channels. Broadcast active."})
            
            generated_quote = f"\"{chat_input}\" — Citizen Report"
            
            st.session_state.stories.insert(0, {
                "id": st.session_state.next_story_id,
                "location": eval_zone if eval_zone != "Other" else "General Delhi",
                "issue": chat_input,
                "quote": generated_quote,
                "timestamp": datetime.datetime.now(),
                "avatar": "⚠️",
                "archived": False
            })
            st.session_state.next_story_id += 1
            st.rerun()

    with col_mid:
        st.subheader("Computed Risk Metrics")
        
        matching_stories = [s for s in active_live_stories if str(s.get("location", "")).lower() == str(eval_zone).lower()]
        res = calculate_risk(str(eval_zone), t1_time.hour, t1_wknd, len(matching_stories))
        
        badge_class = f"badge-{res['level'].lower()}"
        st.markdown(f'<div class="risk-badge {badge_class}">{res["level"]} Risk Level (Score: {res["score"]}/100)</div>', unsafe_allow_html=True)
        
        st.markdown("#### Contributing Logic Vectors:")
        for r in res["reasons"]:
            st.markdown(f"- {r}")
            
        if str(eval_zone) in RISK_ZONES:
            st.markdown("#### Spatial Hazard Map Placement")
            lat = RISK_ZONES[str(eval_zone)]["lat"]
            lon = RISK_ZONES[str(eval_zone)]["lon"]
            m = folium.Map(location=[lat, lon], zoom_start=14)
            folium.Marker([lat, lon], popup=f"{eval_zone}: {res['level']} Risk").add_to(m)
            st_folium(m, height=220, width=420, key=f"map_{eval_zone}")

# ==============================================================================
# TAB 1: RISK BEFORE YOU GO (PART 2 OF 2)
# ==============================================================================
    with col_right:
        st.subheader("🚨 Places on Alert")
        st.caption("Live, user-written alert notes linked to critical hot spots.")
        
        if active_live_stories:
            for story in active_live_stories:
    safe_quote = story.get('quote', f'"{story.get("issue", "Report")}" — Community Alert')
    st.markdown(f"""
    <div class="quote-card">
        <div class="quote-title">📍 {story.get('location', 'General Delhi')}</div>
        <div class="quote-body">{safe_quote}</div>
    </div>
    """, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="text-align:center; padding: 20px; color:#a0aec0; border: 1px dashed #cbd5e0; border-radius:8px;">
                No active hazard quotes logged. System baseline stable.
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    st.markdown("### 📸 Live Crowd-Sourced Safety Stories (Active Feed)")
    st.caption("Active safety stories expire automatically after 48 hours. You can edit script fields, inspect parameters, or manually Archive stories to your User Safety Profile below.")
    
    if active_live_stories:
        story_cols = st.columns(max(len(active_live_stories), 1))
        for idx, story in enumerate(active_live_stories):
            with story_cols[idx]:
                st.markdown(f"""
                <div class="story-container">
                    <div class="story-bubble">{story['avatar']}</div>
                    <div style="margin-top:5px;"><span style="color:#e53e3e; font-weight:800;">● LIVE</span> <b>{story['location']}</b></div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.popover("⚙️ Manage Story", use_container_width=True):
                    st.markdown("Edit Info Details:")
                    story["location"] = st.text_input("Tag Location", value=story["location"], key=f"edit_loc_{story['id']}")
                    story["issue"] = st.text_area("Issue Description", value=story["issue"], key=f"edit_iss_{story['id']}")
                    story["quote"] = st.text_input("Public Wall Quote Note", value=story["quote"], key=f"edit_qte_{story['id']}")
                    
                    if st.button("🗄️ Archive to Profile", key=f"arch_btn_{story['id']}", use_container_width=True):
                        for s_item in st.session_state.stories:
                            if s_item["id"] == story["id"]:
                                s_item["archived"] = True
                        st.success("Story moved safely to profile storage.")
                        st.rerun()
    else:
        blank_cols = st.columns(4)
        with blank_cols:
            st.markdown("""
            <div class="story-container">
                <div class="story-bubble-empty">👤</div>
                <div style="margin-top:5px; color:#718096; font-weight:bold;">@no_active_alerts</div>
                <span style="font-size:0.75rem; color:#a0aec0;">Feed Clear</span>
            </div>
            """, unsafe_allow_html=True)
        with blank_cols:
            st.caption("💡 No Incidents Flagged: The crowdsourced story feed layer is currently empty. Use the Chatbot layout on the left column to log an issue and initiate your location's first visual safety indicator ring token.")

    with st.expander("👤 User Safety Profile & Archived Stories Locker"):
        st.markdown("#### Your Saved / Historical Archive Registry")
        st.caption("Contains citizen safety stories that have passed the 48-hour live expiration threshold, or were manually saved by your session profile framework.")
        
        if archived_profile_stories:
            arch_cols = st.columns(min(len(archived_profile_stories), 6))
            for a_idx, a_story in enumerate(archived_profile_stories):
                with arch_cols[a_idx % 6]:
                    st.markdown(f"""
                    <div style="text-align:center; padding:15px; background-color:#edf2f7; border-radius:12px; margin:5px;">
                        <span style="font-size:2rem;">📁</span>
                        <div style="font-weight:bold; font-size:0.9rem; margin-top:2px;">{a_story['location']}</div>
                        <div style="font-size:0.75rem; color:#718096;">Archived Logs</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.popover("Open Logs", key=f"pop_arch_{a_story['id']}", use_container_width=True):
                        st.write(f"Historical Target Locality: {a_story['location']}")
                        st.write(f"Logged Anomaly Condition: {a_story['issue']}")
                        st.write(f"Stored Public Alert Quote: {a_story['quote']}")
                        if st.button("Unarchive / Bring Live", key=f"unarch_{a_story['id']}"):
                            for s_item in st.session_state.stories:
                                if s_item["id"] == a_story["id"]:
                                    s_item["archived"] = False
                                    s_item["timestamp"] = datetime.datetime.now()
                            st.rerun()
        else:
            st.info("Your historical personal archive database node profile log contains zero saved entries.")

    st.markdown(f'<div class="disclaimer-style">{DISCLAIMER_TEXT}</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 2: WHAT-IF SIMULATOR (PART 1 OF 2)
# ==============================================================================
with tab2:
    st.header("Temporal Multi-Variable Simulation Matrix")
    
    sim_zone = st.selectbox("Select Target Simulation Spot", options=list(RISK_ZONES.keys()), key="t2_zone")
    sim_weekend = st.checkbox("Simulate For Weekend Window?", value=False, key="t2_wknd")
    sim_hour = st.slider("Vary Departure Timeline (24h Clock Axis)", min_value=0, max_value=23, value=12, key="t2_hour_slider")
    
    matching_stories_sim = [s for s in active_live_stories if s["location"].lower() == sim_zone.lower()]
    current_res = calculate_risk(sim_zone, sim_hour, sim_weekend, len(matching_stories_sim))
    
    badge_style = f"badge-{current_res['level'].lower()}"
    st.markdown(f'<div class="risk-badge {badge_style}">Simulated State: {current_res["level"]} Risk Footprint ({current_res["score"]}/100)</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 2: WHAT-IF SIMULATOR (PART 2 OF 2)
# ==============================================================================
    hours_axis = list(range(24))
    scores_axis = [calculate_risk(sim_zone, h, sim_weekend, len(matching_stories_sim))["score"] for h in hours_axis]
    chart_data = pd.DataFrame({"Hour of Day": hours_axis, "Risk Score": scores_axis})
    st.line_chart(chart_data.set_index("Hour of Day"))
    
    future_hours = [(sim_hour + i) % 24 for i in range(1, 6)]
    best_hour = sim_hour
    lowest_score = current_res["score"]
    
    for h in future_hours:
        h_score = calculate_risk(sim_zone, h, sim_weekend, len(matching_stories_sim))["score"]
        if h_score < lowest_score:
            lowest_score = h_score
            best_hour = h
            
    best_res = calculate_risk(sim_zone, best_hour, sim_weekend, len(matching_stories_sim))
    if best_hour != sim_hour:
        st.success(f"💡 **Temporal Safety Mitigation Optimization Matrix:** Adjusting travel plans to **{best_hour:02d}:00** shifts risk boundaries down to a **{best_res['level']}** level.")
    else:
        st.info("💡 Selected timestamp frame corresponds to the absolute mathematical lowest baseline for this sector.")
        
    st.markdown(f'<div class="disclaimer-style">{DISCLAIMER_TEXT}</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 3: PRETEND CALL (COMPLETE ARCHITECTURE NODE)
# ==============================================================================
with tab3:
    st.header("Situational De-escalation Virtual Check-In Screen")
    
    for idx in range(len(st.session_state.contacts)):
        if idx >= len(st.session_state.contacts): break
        c = st.session_state.contacts[idx]
        row_id = c["id"]
        
        c_col1, c_col2, c_col3, c_col4 = st.columns([1.5, 1, 3, 1.5])
        
        with c_col1:
            new_name = st.text_input(f"Name Input #{row_id}", value=c["name"], key=f"name_field_{row_id}", label_visibility="collapsed")
            st.session_state.contacts[idx]["name"] = new_name
        with c_col2:
            new_gender = st.selectbox(f"Gender Select #{row_id}", ["Male", "Female"], index=0 if c["gender"] == "Male" else 1, key=f"gender_field_{row_id}", label_visibility="collapsed")
            st.session_state.contacts[idx]["gender"] = new_gender
        with c_col3:
            st.caption(f"**[{c.get('relation','Contact')}]** \"{c['script'][:55]}...\"")
        with c_col4:
            sub1, sub2 = st.columns(2)
            with sub1:
                if st.button("📞", key=f"trigger_call_btn_{row_id}"): st.session_state.active_call = st.session_state.contacts[idx]
            with sub2:
                if st.button("🗑️", key=f"delete_node_btn_{row_id}"):
                    st.session_state.contacts.pop(idx)
                    st.rerun()
                    
    with st.expander("➕ Configure Custom Contact Profile Node"):
        new_c_name = st.text_input("Name Identifier", key="add_c_name")
        new_c_rel = st.text_input("Relationship Structure (e.g. Police, Guard)", key="add_c_rel")
        new_c_gender = st.selectbox("Vocal Gender Assignment Profile", ["Male", "Female"], key="add_c_gender")
        new_c_script = st.text_area("Custom TTS Prompt Script", value="I am tracking your navigation route coordinates live. Keep talking to me.", key="add_c_script")
        uploaded_voice = st.file_uploader("Upload Direct Audio File Override (WAV/MP3)", type=["wav", "mp3"], key="add_c_audio")
        
        if st.button("Save Profile Structure", key="add_c_submit_btn"):
            if new_c_name:
                audio_data = uploaded_voice.read() if uploaded_voice is not None else None
                st.session_state.contacts.append({
                    "id": st.session_state.next_id,
                    "name": new_c_name,
                    "relation": new_c_rel,
                    "gender": new_c_gender,
                    "script": new_c_script,
                    "audio_bytes": audio_data
                })
                st.session_state.next_id += 1
                st.success("New contact configured successfully.")
                st.rerun()
                
    if st.session_state.active_call is not None:
        target = st.session_state.active_call
        st.markdown("---")
        
        st.markdown(f"""
        <div class="phone-screen">
            <div style="font-size: 0.8rem; color: #a0aec0; letter-spacing: 2px; margin-bottom: 5px;">ALERT HER INCOMING CONNECTION</div>
            <div style="font-size: 2rem; font-weight: bold; margin-bottom: 5px;">{target['name']}</div>
            <div style="font-size: 1rem; color: #cbd5e0; margin-bottom: 5px;">({target.get('relation','Contact')})</div>
            <div style="font-size: 0.85rem; color: #dd8c2b; margin-bottom: 30px;">Voice Profile Channel: {target['gender']} Voice</div>
            <div style="font-size: 4rem; margin-bottom: 40px;">👤</div>
            <div style="display: flex; justify-content: space-around; width: 100%;">
                <div style="background-color: #2f9e44; padding: 15px; border-radius: 50%; width: 55px; height: 55px;"></div>
                <div style="background-color: #e53e3e; padding: 15px; border-radius: 50%; width: 55px; height: 55px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if target["audio_bytes"] is not None:
            st.audio(target["audio_bytes"], format="audio/mp3")
        else:
            with st.spinner("Synthesizing gendered audio output stream..."):
                if target["gender"] == "Male":
                    tts = gTTS(text=target["script"], lang='en', tld='co.uk')
                else:
                    tts = gTTS(text=target["script"], lang='en', tld='com')
                    
                temp_file = f"call_{target['id']}.mp3"
                tts.save(temp_file)
                
                with open(temp_file, "rb") as f:
                    generated_bytes = f.read()
                st.audio(generated_bytes, format="audio/mp3", autoplay=True)
                
                try: os.remove(temp_file)
                except OSError: pass
                    
        if st.button("Disconnect Call Overlay Frame", key="disconnect_call_btn"):
            st.session_state.active_call = None
            st.rerun()

