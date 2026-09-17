import streamlit as st
import pandas as pd
import datetime
import os
import base64
from gtts import gtts
from risk_engine import RISK_ZONES, calculate_risk

# Component verification safety boundaries
try:
    import folium
    from streamlit_folium import st_folium
except ImportError:
    st.error("Missing critical mapping libraries. Please ensure streamlit-folium and folium are provisioned.")

st.set_page_config(page_title="Alert Her", page_icon="🛡️", layout="wide")

# --- SYSTEM WIDE CUSTOM ANIMATED CSS LAYOUT ---
st.markdown("""
<style>
    .main-title { font-size: 2.6rem; font-weight: 800; color: #e53e3e; margin-bottom: 0px; }
    .tagline { font-size: 1.1rem; color: #4a5568; margin-bottom: 25px; }
    .risk-badge {
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.3rem;
        display: inline-block;
        color: white;
        text-align: center;
        margin-bottom: 15px;
    }
    .badge-low { background-color: #2f9e44; }
    .badge-moderate { background-color: #dd8c2b; }
    .badge-high {
        background-color: #e53e3e;
        box-shadow: 0 0 0 0 rgba(229, 62, 62, 1);
        animation: pulse-red 2s infinite;
    }
    @keyframes pulse-red {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(229, 62, 62, 0.7); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 10px rgba(229, 62, 62, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(229, 62, 62, 0); }
    }
    .story-ring {
        border: 3px solid #e53e3e;
        border-radius: 50%;
        width: 75px;
        height: 75px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 8px auto;
        background-color: #fff;
        cursor: pointer;
        animation: ring-glow 1.5s ease-in-out infinite alternate;
    }
    @keyframes ring-glow {
        0% { border-color: #e53e3e; box-shadow: 0 0 5px rgba(229,62,62,0.5); }
        100% { border-color: #dd8c2b; box-shadow: 0 0 15px rgba(221,140,43,0.8); }
    }
    .story-container { text-align: center; margin: 10px; padding: 5px; }
    .story-tag { font-size: 0.85rem; font-weight: bold; color: #2d3748; display: block; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }
    .phone-frame {
        background-color: #1a202c;
        border: 4px solid #4a5568;
        border-radius: 24px;
        padding: 40px 20px;
        text-align: center;
        color: white;
        max-width: 320px;
        margin: 20px auto;
    }
    .academic-disclaimer {
        font-size: 0.85rem;
        color: #718096;
        text-align: center;
        margin-top: 40px;
        padding: 15px;
        border-top: 1px dashed #cbd5e0;
        line-height: 1.4;
    }
</style>
""", unsafe_content_html=True)

# --- REPOSITORIES SHARED INITIALIZATION LAYERS ---
if "stories" not in st.session_state:
    st.session_state.stories = [
        {"location": "ITO", "time": "11:45 AM", "issue": "Severe streetlight failure along metro access corridor. Path dark.", "avatar": "⚠️"},
        {"location": "Sultanpuri", "time": "12:15 PM", "issue": "Crowded unregulated assembly near market gate. Avoid narrow lanes.", "avatar": "🚨"},
        {"location": "Vasant Vihar", "time": "10:30 AM", "issue": "Suspicious loitering near campus back gate reported.", "avatar": "👀"}
    ]

if "contacts" not in st.session_state:
    st.session_state.contacts = [
        {"id": 0, "name": "Mom", "relation": "Mother", "script": "Hey beta, where are you? I am waiting outside for you, please call me back as soon as you see this.", "gender": "Female", "audio_bytes": None},
        {"id": 1, "name": "Dad", "relation": "Father", "script": "Beta, have you boarded your ride yet? Share your live location right now.", "gender": "Male", "audio_bytes": None},
        {"id": 2, "name": "Dr. Sharma", "relation": "Doctor", "script": "This is Dr. Sharma's clinic. Your medical reports are ready for collection, please call back tomorrow.", "gender": "Male", "audio_bytes": None},
        {"id": 3, "name": "Kriti", "relation": "Sister", "script": "Hey! I am reached the restaurant already, where are you stuck? Hurry up, I'm ordering food.", "gender": "Female", "audio_bytes": None},
        {"id": 4, "name": "Rahul", "relation": "Brother", "script": "Listen, I am standing near the metro gate number 2. Walk fast, I can see your train arrived.", "gender": "Male", "audio_bytes": None}
    ]
if "next_id" not in st.session_state: st.session_state.next_id = 5
if "active_call" not in st.session_state: st.session_state.active_call = None

# App Layout Headings
st.markdown('<p class="main-title">🛡️ Alert Her</p>', unsafe_content_html=True)
st.markdown('<p class="tagline">Personalized Safety Navigation & Crowd-Sourced Risk Mitigator</p>', unsafe_content_html=True)

tab1, tab2, tab3 = st.tabs(["📍 Risk Before You Go", "📉 What-If Simulator", "📞 Pretend Call"])

# ==============================================================================
# TAB 1: RISK BEFORE YOU GO (WITH AI CHATBOT & FLASHING INSTAGRAM STORIES)
# ==============================================================================
with tab1:
    st.subheader("Predictive Location Screening & Live Threat Feeds")
    
    t1_left, t1_right = st.columns([1, 1])
    
    with t1_left:
        st.markdown("### Route Matrix Parameters")
        zone_options = list(RISK_ZONES.keys()) + ["Other"]
        eval_zone = st.selectbox("Target Locality Target Node", options=zone_options, key="t1_dest")
        
        if eval_zone == "Other":
            custom_input = st.text_input("Enter Custom Delhi Locality Name:", value="", placeholder="Type area...")
            target_lookup = custom_input if custom_input else "Other"
        else:
            target_lookup = eval_zone
            
        t1_time = st.time_input("Target Execution Time", value=datetime.datetime.now().time())
        t1_wknd = st.checkbox("Weekend Travel Profile Check", value=datetime.date.today().weekday() >= 5)
        
        # Sub-Section: AI Assistant Intake Pipeline
        st.markdown("#### 🤖 AI Safety Assistant Chatbot")
        st.caption("Submit anonymous dynamic logs here to tag active risks for all platform users instantly.")
        
        chat_query = st.chat_input("Log an active hazard (e.g. 'Street lights broken near metro gate')...")
        if chat_query:
            st.info(f"**AI Assistant:** Safety broadcast processing node acknowledged. Broadcasting '{chat_query}' tagged to **{target_lookup}** across active network layers.")
            st.session_state.stories.insert(0, {
                "location": target_lookup,
                "time": "Just Now",
                "issue": chat_query,
                "avatar": "🔔"
            })
            
    with t1_right:
        st.markdown("### Risk Engine Analytical Output")
        res = calculate_risk(target_lookup, t1_time.hour, t1_wknd)
        
        badge_style = f"badge-{res['level'].lower()}"
        st.markdown(f'<div class="risk-badge {badge_style}">{res["level"]} Risk State (Score: {res["score"]}/100)</div>', unsafe_content_html=True)
        
        st.markdown("**Core Contributing Safety Vectors:**")
        for r in res["reasons"]:
            st.markdown(f"- {r}")
            
        if target_lookup in RISK_ZONES:
            lat, lon = RISK_ZONES[target_lookup]["lat"], RISK_ZONES[target_lookup]["lon"]
            m = folium.Map(location=[lat, lon], zoom_start=14)
            folium.Marker([lat, lon], popup=f"{target_lookup}: Tier Risk Eval").add_to(m)
            st_folium(m, height=220, width=500, key="t1_map_vector")

    # Interactive Crowdsourced Visual Feed Section (Instagram Stories Emulation Layout)
    st.markdown("---")
    st.markdown("### 📸 Live Crowdsourced Safety Stories")
    st.caption("Flashing indicator matrices mark local conditions flagged by recent users within the network framework. Click to display detail overlays.")
    
    story_cols = st.columns(max(len(st.session_state.stories), 1))
    for idx, story in enumerate(st.session_state.stories):
        with story_cols[idx % len(story_cols)]:
            st.markdown(f"""
            <div class="story-container">
                <div class="story-ring"><span style="font-size:2rem;">{story['avatar']}</span></div>
                <span class="story-tag">🚨 {story['location']}</span>
                <span style="font-size:0.75rem; color:#a0aec0;">{story['time']}</span>
            </div>
            """, unsafe_content_html=True)
            if st.button("Review Update Log", key=f"story_btn_{idx}", use_container_width=True):
                st.warning(f"**Live Incident Vector [{story['location']} - {story['time']}]:** {story['issue']}")

    st.markdown('<p class="academic-disclaimer">Disclaimer: The safety score and risk index computed by this application are derived strictly from historical crime metrics, geographical reporting trends, and crowd-sourced inputs. They do not constitute personalized security guarantees or reflect live real-time crime tracking.</p>', unsafe_content_html=True)

# ==============================================================================
# TAB 2: WHAT-IF SIMULATOR
# ==============================================================================
with tab2:
    st.subheader("Dynamic Temporal Simulation Sandbox")
    
    sim_zone = st.selectbox("Select Target Simulation Zone Node", options=list(RISK_ZONES.keys()), key="t2_dest")
    sim_wknd = st.checkbox("Simulate Target Weekend Matrix Alterations", value=False, key="t2_wknd")
    
    sim_hour = st.slider("Vary Simulation Execution Hour (24h format)", min_value=0, max_value=23, value=datetime.datetime.now().hour)
    
    live_res = calculate_risk(sim_zone, sim_hour, sim_wknd)
    live_badge = f"badge-{live_res['level'].lower()}"
