"""
app.py — Digital Twin AI-Based Adaptive Power Amplifier (website)
--------------------------------------------------------------
This is the ONLY file with website code in it. All AI/math logic lives
in pa_core.py. This file just draws tabs/buttons and shows results.

Run locally with:   streamlit run app.py
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from risk_engine import RISK_ZONES, calculate_risk


st.set_page_config(page_title="AI Digital Twin — Power Amplifier", layout="wide")

# ------------------------------------------------------------------
# Session state = "memory" of the website while it's open, so results
# from one tab (e.g. the trained twin) are available in later tabs.
# ------------------------------------------------------------------
if "data" not in st.session_state:
    st.session_state.data = None
if "twin" not in st.session_state:
    st.session_state.twin = None
if "thermal" not in st.session_state:
    st.session_state.thermal = None
if "opt" not in st.session_state:
    st.session_state.opt = None
if "loop" not in st.session_state:
    st.session_state.loop = None

# ------------------------------------------------------------------
# Sidebar — shows the professor's exact architecture flow
# ------------------------------------------------------------------
st.sidebar.title("System Architecture")
st.sidebar.markdown(
    """
    **Closed-Loop AI + Digital Twin flow:**

    1. Physical PA → Sensors
    2. Data Acquisition
    3. Digital Twin Engine
    4. Hybrid Physics–AI Model
    5. State Estimation (thermal/aging)
    6. AI Optimizer (Bayesian)
    7. Adaptive Control → back to PA
    """
)
st.sidebar.info("Use the tabs to run each block in order (1→5). Each block feeds the next.")

st.title("🔧 AI-Based Digital Twin for Adaptive Power Amplifier Control")
st.caption("Digital Twin–Assisted AI-Based Adaptive Power Amplifier for Real-Time Optimization and Predictive Control")

tabs = st.tabs([
    "🏠 Home",
    "1️⃣ Data Acquisition",
    "2️⃣ Digital Twin (AI Model)",
    "3️⃣ State Estimation (Thermal/Aging)",
    "4️⃣ AI Optimizer",
    "5️⃣ Closed-Loop Simulation",
])

# ==================================================================
# TAB: HOME
# ==================================================================
with tabs[0]:
    st.header("Project Overview")
    st.markdown(
        """
        This site implements an **AI-based Digital Twin** for a Class-F⁻¹ RF power
        amplifier, following the closed-loop architecture shown in the sidebar.

        Because this project was built remotely without lab/RF hardware access,
        all data below is **simulated** from a memory-polynomial reference model
        (a standard PA-modeling equation), used as a stand-in for real measurement
        data. Every model shown here is **actually trained live** when you press
        the buttons — nothing is pre-baked or fake.

        **How to use this site:** go through the tabs in order, 1 → 5. Each block
        needs the previous one to have been run at least once.
        """
    )
    st.subheader("Governing equation being modeled")
    st.latex(r"y(n) = F(x(n), x(n-1), ..., x(n-M), V_{GS}, V_{DS}, T_j, \theta_d) + \varepsilon(n)")

# ==================================================================
# TAB 1: DATA ACQUISITION  (Block 0)
# ==================================================================
with tabs[1]:
    st.header("Block 1 — Physical PA (simulated) + Sensors + Data Acquisition")
    st.markdown("Generates simulated PA input/output signal data, bias voltages, and junction temperature — standing in for real sensor measurements.")

    n_samples = st.slider("Number of samples", 1000, 10000, 6000, step=500)

    if st.button("▶ Generate Data", type="primary"):
        with st.spinner("Simulating PA and sensor readings..."):
            st.session_state.data = pc.generate_pa_data(n_samples=n_samples)
        st.success(f"Generated {n_samples} samples.")

    if st.session_state.data is not None:
        d = st.session_state.data
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(5, 3))
            ax.plot(d["x"][:200], label="Input x(n)")
            ax.plot(d["y"][:200], label="Output y(n)", alpha=0.8)
            ax.set_xlabel("Sample index"); ax.legend(); ax.set_title("PA Input vs Output (sample)")
            st.pyplot(fig)
        with col2:
            fig, ax = plt.subplots(figsize=(5, 3))
            ax.plot(d["Tj"][:500], color="tomato")
            ax.set_xlabel("Sample index"); ax.set_ylabel("Junction Temp (°C)")
            ax.set_title("Simulated Thermal Drift")
            st.pyplot(fig)
        st.dataframe(
            {"x(n)": d["x"][:10], "Vgs": d["Vgs"][:10], "Vds": d["Vds"][:10],
             "Tj": d["Tj"][:10], "y(n)": d["y"][:10]}
        )

# ==================================================================
# TAB 2: DIGITAL TWIN  (Block 1+2)
# ==================================================================
with tabs[2]:
    st.header("Block 2 — Digital Twin Engine (Neural Network Behavioral Model)")
    st.markdown("Trains a neural network to learn the PA's nonlinear input→output mapping. The physics slider adds a smoothness constraint approximating a physics-informed loss term.")

    physics_weight = st.slider("Physics-informed weight (λ_physics)", 0.0, 1.0, 0.5, step=0.1)

    if st.session_state.data is None:
        st.warning("⬅ Run Block 1 (Data Acquisition) first.")
    else:
        if st.button("▶ Train Digital Twin", type="primary"):
            with st.spinner("Training neural network..."):
                st.session_state.twin = pc.train_digital_twin(st.session_state.data, physics_weight)
            st.success("Digital Twin trained.")

        if st.session_state.twin is not None:
            t = st.session_state.twin
            c1, c2 = st.columns(2)
            c1.metric("Test NMSE", f"{t['nmse_db']:.2f} dB")
            c2.metric("Test MSE", f"{t['mse']:.5f}")

            fig, ax = plt.subplots(figsize=(5, 4))
            ax.scatter(t["y_test"], t["y_pred"], s=6, alpha=0.4)
            lims = [min(t["y_test"].min(), t["y_pred"].min()), max(t["y_test"].max(), t["y_pred"].max())]
            ax.plot(lims, lims, "r--")
            ax.set_xlabel("Actual"); ax.set_ylabel("Predicted")
            ax.set_title("Digital Twin: Predicted vs Actual")
            st.pyplot(fig)

            fig2, ax2 = plt.subplots(figsize=(5, 3))
            ax2.plot(t["loss_curve"], color="green")
            ax2.set_xlabel("Training iteration"); ax2.set_ylabel("Loss")
            ax2.set_title("Training Convergence")
            st.pyplot(fig2)

# ==================================================================
# TAB 3: STATE ESTIMATION  (Block 3)
# ==================================================================
with tabs[3]:
    st.header("Block 3 — State Estimation: Thermal / Aging Drift Prediction")
    st.markdown("Predicts future junction temperature from a short window of past readings (sequence prediction).")

    if st.session_state.data is None:
        st.warning("⬅ Run Block 1 (Data Acquisition) first.")
    else:
        if st.button("▶ Train Thermal Predictor", type="primary"):
            with st.spinner("Training thermal/aging predictor..."):
                st.session_state.thermal = pc.train_thermal_predictor(st.session_state.data)
            st.success("Thermal predictor trained.")

        if st.session_state.thermal is not None:
            th = st.session_state.thermal
            st.metric("Prediction MSE", f"{th['mse']:.4f} °C²")

            fig, ax = plt.subplots(figsize=(7, 3.5))
            order = np.argsort(np.arange(len(th["y_test"])))
            ax.plot(th["y_test"][:150], label="Actual Tj")
            ax.plot(th["y_pred"][:150], label="Predicted Tj", linestyle="--")
            ax.set_xlabel("Sample"); ax.set_ylabel("Temperature (°C)")
            ax.legend(); ax.set_title("Thermal Drift: Predicted vs Actual")
            st.pyplot(fig)

# ==================================================================
# TAB 4: AI OPTIMIZER  (Block 4)
# ==================================================================
with tabs[4]:
    st.header("Block 4 — AI Engine: Bayesian Multi-Objective Optimizer")
    st.markdown("Searches for the bias point (Vgs, Vds) that maximizes an efficiency proxy while minimizing a distortion proxy, using the trained Digital Twin as a fast virtual PA.")

    n_calls = st.slider("Optimization iterations", 10, 40, 20, step=5)

    if st.session_state.twin is None:
        st.warning("⬅ Run Block 2 (Digital Twin) first.")
    else:
        if st.button("▶ Run Optimizer", type="primary"):
            with st.spinner("Running Bayesian optimization..."):
                st.session_state.opt = pc.bayesian_optimize_bias(
                    st.session_state.twin, st.session_state.data, n_calls=n_calls
                )
            st.success("Optimization complete.")

        if st.session_state.opt is not None:
            o = st.session_state.opt
            c1, c2, c3 = st.columns(3)
            c1.metric("Best Vgs", f"{o['best_Vgs']:.3f} V")
            c2.metric("Best Vds", f"{o['best_Vds']:.3f} V")
            c3.metric("Best Score", f"{o['best_score']:.4f}")

            fig, ax = plt.subplots(figsize=(6, 3.5))
            running_best = np.maximum.accumulate(o["history"])
            ax.plot(o["history"], "o-", alpha=0.4, label="Trial score")
            ax.plot(running_best, "r-", linewidth=2, label="Best so far")
            ax.set_xlabel("Iteration"); ax.set_ylabel("Score (efficiency − distortion)")
            ax.legend(); ax.set_title("Bayesian Optimization Progress")
            st.pyplot(fig)

# ==================================================================
# TAB 5: CLOSED LOOP  (Block 5)
# ==================================================================
with tabs[5]:
    st.header("Block 5 — Closed-Loop Adaptive Control (everything connected)")
    st.markdown("Runs the full loop: Digital Twin predicts output → optimized bias applied → thermal model predicts next state → repeat.")

    steps = st.slider("Simulation steps", 20, 150, 60, step=10)

    if st.session_state.twin is None or st.session_state.thermal is None or st.session_state.opt is None:
        st.warning("⬅ Run Blocks 2, 3, and 4 first — this block connects all of them.")
    else:
        if st.button("▶ Run Closed-Loop Simulation", type="primary"):
            with st.spinner("Running closed-loop simulation..."):
                st.session_state.loop = pc.run_closed_loop(
                    st.session_state.twin, st.session_state.thermal,
                    st.session_state.opt, st.session_state.data, steps=steps
                )
            st.success("Closed-loop simulation complete.")

        if st.session_state.loop is not None:
            lp = st.session_state.loop
            st.markdown(f"Running at optimized bias: **Vgs = {lp['Vgs']:.3f} V, Vds = {lp['Vds']:.3f} V**")

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
            ax1.plot(lp["outputs"], color="steelblue")
            ax1.set_ylabel("PA Output (predicted)")
            ax1.set_title("Closed-Loop Simulation Over Time")

            ax2.plot(lp["temps"], color="tomato")
            ax2.set_ylabel("Junction Temp (°C)")
            ax2.set_xlabel("Time step")
            st.pyplot(fig)

            st.success("✅ Full pipeline connected: Data → Digital Twin → Optimizer → Control → back to PA.")
