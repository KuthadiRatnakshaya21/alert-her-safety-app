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

# --- DATA STATE MEMORY LAYERS INITIALIZATION ---
if "stories" not in st.session_state:
    st.session_state.stories = [
        {"timestamp": "10 Mins Ago", "location": "ITO", "issue": "Broken street lights near metro gate 2, deserted stretch.", "avatar": "⚠️"},
        {"timestamp": "45 Mins Ago", "location": "Sultanpuri", "issue": "Heavy crowding and rowdy groups gathered near market area.", "avatar": "🚨"}
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
if "active_call" not in st.session_state: st.session_state.active_call = None

# --- SYSTEM WIDE ANIMATED LAYOUT CSS CONFIGURATION ---
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
    @keyframes story-glow {
        0% { border-color: #e53e3e; box-shadow: 0 0 5px rgba(229,62,62,0.4); }
        100% { border-color: #dd8c2b; box-shadow: 0 0 12px rgba(221,140,43,0.7); }
    }
    .story-container { text-align: center; margin: 10px; font-weight: bold; font-size: 0.9rem; }
    .phone-screen {
        background-color: #1a202c; border: 4px solid #4a5568; border-radius: 24px;
        padding: 40px 20px; text-align: center; color: white; max-width: 320px; margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🛡️ ALERT HER — A Women\'s Safety App</p>', unsafe_allow_html=True)
st.markdown('<p class="tagline">An AI-first safety app that predicts risk before travel, suggests safer decisions, and finds nearby help—preventing emergencies instead of reacting to them.</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📍 Risk Before You Go", "📉 What-If Simulator", "📞 Pretend Call"])

DISCLAIMER_TEXT = "Disclaimer: The safety score and operational risk matrices computed by this application are derived strictly from historical crime metrics, geographical reporting trends, and crowd-sourced user inputs. They do not constitute personalized security guarantees or reflect live real-time crime tracking."

# ==============================================================================
# TAB 1: RISK BEFORE YOU GO
# ==============================================================================
with tab1:
    st.header("Location Safety Evaluation & Live Incidents")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Configure Travel Vector")
        zone_options = list(RISK_ZONES.keys()) + ["Other (Custom Location)"]
        selected_zone = st.selectbox("Select Target Destination", options=zone_options, key="tab1_zone_select")
        
        if selected_zone == "Other (Custom Location)":
            custom_name = st.text_input("Enter Locality Name", value="", key="tab1_custom_name")
            eval_zone = custom_name if custom_name else "Other"
        else:
            eval_zone = selected_zone
            
        t1_time = st.time_input("Planned Departure Time", value=datetime.datetime.now().time(), key="tab1_time_input")
        t1_wknd = st.checkbox("Traveling on a Weekend?", key="tab1_weekend_chk")
        
        st.markdown("---")
        st.subheader("💬 AI Safety Assistant Chatbot")
        st.caption("Report micro-hazards or suspicious activities along routes to flag coordinates instantly.")
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["text"])
                
        if chat_input := st.chat_input("Type your hazard update (e.g. 'Poorly lit section near access gates')...", key="tab1_chat_field"):
            st.session_state.chat_history.append({"role": "user", "text": chat_input})
            st.session_state.chat_history.append({"role": "assistant", "text": "Hazard update parsed successfully. Broad-casting geotag details to flashing stories modules."})
            
            st.session_state.stories.insert(0, {
                "timestamp": "Just Now",
                "location": eval_zone if eval_zone != "Other" else "General Delhi",
                "issue": chat_input,
                "avatar": "⚠️"
            })
            st.rerun()

    with col_right:
        st.subheader("Computed Risk Metrics")
        
        matching_stories = [s for s in st.session_state.stories if s["location"].lower() == str(eval_zone).lower()]
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
            st_folium(m, height=250, width=500, key=f"map_{eval_zone}")
            
    # Flashing Instagram Stories Emulation Dashboard Feed
    st.markdown("### 📸 Live Crowd-Sourced Safety Feeds (Flash Alerts)")
    st.caption("Click any glowing marker bubble below to review active safety reports submitted by local drivers or commuters.")
    
    if st.session_state.stories:
        story_cols = st.columns(min(len(st.session_state.stories), 7))
        for idx, story in enumerate(st.session_state.stories[:7]):
            with story_cols[idx]:
                st.markdown(f'<div class="story-bubble">{story["avatar"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="story-container">{story["location"]}<br><span style="font-size:0.75rem; color:#718096;">{story["timestamp"]}</span></div>', unsafe_allow_html=True)
                if st.button("Inspect Logs", key=f"btn_story_{idx}", use_container_width=True):
                    st.info(f"**Live Condition Anomaly [{story['location']} - {story['timestamp']}]:** {story['issue']}")
    else:
        st.write("No active alert matrix signatures loaded inside current timeline window.")
        
    st.markdown(f'<div class="disclaimer-style">{DISCLAIMER_TEXT}</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 2: WHAT-IF SIMULATOR
# ==============================================================================
with tab2:
    st.header("Temporal Multi-Variable Simulation Matrix")
    
    sim_zone = st.selectbox("Select Target Simulation Spot", options=list(RISK_ZONES.keys()), key="t2_zone")
    sim_weekend = st.checkbox("Simulate For Weekend Window?", value=False, key="t2_wknd")
    sim_hour = st.slider("Vary Departure Timeline (24h Clock Axis)", min_value=0, max_value=23, value=12, key="t2_hour_slider")
    
