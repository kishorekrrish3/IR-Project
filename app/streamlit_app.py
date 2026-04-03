import streamlit as st
import requests

st.set_page_config(
    page_title="Insurance Fraud Detector",
    page_icon="🔍",
    layout="wide"
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .score-card {
        background: linear-gradient(135deg, #1e2130, #252b3b);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #2d3450;
    }
    .score-value { font-size: 3rem; font-weight: 800; }
    .score-label { font-size: 0.9rem; color: #aaa; margin-top: 4px; }
    .risk-HIGH   { color: #ff4b4b; }
    .risk-MEDIUM { color: #ffa500; }
    .risk-LOW    { color: #00c87a; }
    .nlp-detail  { font-size: 0.85rem; color: #ccc; padding: 4px 0; }
    .sample-btn  { font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.title("🔍 Dual-Channel Insurance Fraud Detector")
st.markdown(
    "Analyses both **structured claim data** and **free-text narratives** independently, "
    "then combines them into a final fraud risk score."
)

# ─────────────────────────────────────────────────────────────────────────────
# Sample text buttons
# ─────────────────────────────────────────────────────────────────────────────
FRAUD_SAMPLE = (
    "The accident happened suddenly and I cannot clearly remember exactly what occurred. "
    "It was very fast and there were no witnesses around at the time. My car was seriously "
    "damaged, much more than it looks, and I need urgent processing of my maximum claim amount "
    "as I am in a very difficult financial situation right now. The other driver left before "
    "police arrived. I have been a loyal customer for years and urgently need this approved."
)

LEGIT_SAMPLE = (
    "On March 14th at approximately 3:45 PM, while I was driving north on Oak Street, a silver "
    "Toyota Camry ran a red light at the intersection of Oak and Main and struck my vehicle on "
    "the driver's side. Two witnesses, Mrs. Sarah Collins and Mr. James Reid, were present and "
    "have provided their contact details. Police report #2024-1234 was filed by Officer Williams. "
    "I have attached repair quotes ranging from $2,800 to $3,500 and photos of the scene."
)

col_fraud_btn, col_legit_btn, _ = st.columns([1, 1, 4])
load_fraud = col_fraud_btn.button("📋 Load Fraudulent Sample", key="load_fraud")
load_legit = col_legit_btn.button("📋 Load Legitimate Sample", key="load_legit")

if load_fraud:
    st.session_state['claim_text'] = FRAUD_SAMPLE
if load_legit:
    st.session_state['claim_text'] = LEGIT_SAMPLE

# ─────────────────────────────────────────────────────────────────────────────
# Two-column layout: Left = Text, Right = Structured
# ─────────────────────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.subheader("📝 Channel B — Claim Narrative")
    st.markdown("*Emails, letters, free-text descriptions*")
    claim_text = st.text_area(
        "Claim description / Email / Letter",
        value=st.session_state.get('claim_text', ''),
        height=220,
        placeholder="Describe the incident... (paste an email, letter, or narrative)",
        label_visibility="collapsed",
    )

with right_col:
    st.subheader("📊 Channel A — Structured Claim Data")
    st.markdown("*Form fields from the insurance claim*")

    c1, c2 = st.columns(2)
    with c1:
        age      = st.number_input("Age", 18, 100, 45)
        months   = st.number_input("Months as Customer", 0, 500, 200)
        premium  = st.number_input("Policy Premium ($/yr)", 0.0, 10000.0, 1200.0)
        umbrella = st.number_input("Umbrella Limit ($)", 0.0, 1_000_000.0, 0.0)
    with c2:
        hour     = st.slider("Incident Hour", 0, 23, 2)
        vehicles = st.number_input("Vehicles Involved", 1, 10, 2)
        injuries = st.number_input("Bodily Injuries", 0, 5, 2)
        witnesses = st.number_input("Witnesses", 0, 10, 0)

    c3, c4 = st.columns(2)
    with c3:
        total_claim   = st.number_input("Total Claim ($)", 0.0, 200_000.0, 80_000.0)
        injury_claim  = st.number_input("Injury Claim ($)", 0.0, 100_000.0, 30_000.0)
    with c4:
        property_claim = st.number_input("Property Claim ($)", 0.0, 100_000.0, 20_000.0)
        vehicle_claim  = st.number_input("Vehicle Claim ($)", 0.0, 100_000.0, 30_000.0)

    incident_type     = st.selectbox("Incident Type", [
        "Single Vehicle Collision", "Multi-vehicle Collision", "Parked Car", "Vehicle Theft"
    ])
    incident_severity = st.selectbox("Incident Severity", [
        "Minor Damage", "Major Damage", "Total Loss", "Trivial Damage"
    ])

# ─────────────────────────────────────────────────────────────────────────────
# Analyze button
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
analyze = st.button("🔍 Analyze Claim (Dual-Channel)", use_container_width=True, type="primary")

if analyze:
    if not claim_text.strip():
        st.warning("⚠️ Please enter a claim narrative in Channel B (left side).")
    else:
        payload = {
            "age": age,
            "months_as_customer": months,
            "policy_annual_premium": premium,
            "umbrella_limit": umbrella,
            "incident_hour_of_the_day": hour,
            "number_of_vehicles_involved": vehicles,
            "bodily_injuries": injuries,
            "witnesses": witnesses,
            "total_claim_amount": total_claim,
            "injury_claim": injury_claim,
            "property_claim": property_claim,
            "vehicle_claim": vehicle_claim,
            "incident_type": incident_type,
            "incident_severity": incident_severity,
            "claim_text": claim_text,
        }

        with st.spinner("Analysing claim through dual-channel pipeline..."):
            try:
                resp = requests.post("http://127.0.0.1:8000/analyze-claim", json=payload, timeout=30)

                if resp.status_code == 200:
                    r = resp.json()

                    if "error" in r:
                        st.error(f"API Error: {r['error']}")
                    else:
                        # ─── Score Cards ─────────────────────────────────────
                        st.subheader("📊 Results")
                        sc1, sc2, sc3 = st.columns(3)

                        risk = r.get("risk_level", "LOW")
                        risk_cls = f"risk-{risk}"
                        risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk, "⚪")

                        with sc1:
                            st.markdown(f"""
                            <div class="score-card">
                                <div class="score-value {risk_cls}">{r['final_score']}</div>
                                <div class="score-label">Final Fraud Score / 100</div>
                                <div style="margin-top:8px;font-size:1.1rem">{risk_emoji} {risk} RISK</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with sc2:
                            struct_color = "risk-HIGH" if r['structured_score'] >= 60 else \
                                           "risk-MEDIUM" if r['structured_score'] >= 30 else "risk-LOW"
                            st.markdown(f"""
                            <div class="score-card">
                                <div class="score-value {struct_color}">{r['structured_score']}</div>
                                <div class="score-label">Channel A — Structured Data Score</div>
                                <div style="margin-top:8px;font-size:0.8rem;color:#888">
                                    XGBoost on form fields
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        with sc3:
                            nlp_color = "risk-HIGH" if r['nlp_score'] >= 60 else \
                                        "risk-MEDIUM" if r['nlp_score'] >= 30 else "risk-LOW"
                            st.markdown(f"""
                            <div class="score-card">
                                <div class="score-value {nlp_color}">{r['nlp_score']}</div>
                                <div class="score-label">Channel B — NLP Text Score</div>
                                <div style="margin-top:8px;font-size:0.8rem;color:#888">
                                    Semantic + keyword analysis
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        st.divider()

                        # ─── NLP Breakdown ───────────────────────────────────
                        detail_col, shap_col = st.columns(2)

                        with detail_col:
                            st.subheader("🧠 NLP Signal Breakdown")
                            bd = r.get("nlp_breakdown", {})
                            if bd:
                                metrics = {
                                    "Semantic Similarity": bd.get("semantic_similarity", 0),
                                    "Fraud Keyword Density": bd.get("keyword_density", 0),
                                    "Vagueness / Hedges": bd.get("vagueness_score", 0),
                                    "Sentiment Suspicion": bd.get("sentiment_suspicion", 0),
                                    "Specificity (↓ = suspicious)": bd.get("specificity_score", 0),
                                }
                                for label, val in metrics.items():
                                    bar_pct = int(val * 100)
                                    color = "#ff4b4b" if val > 0.6 else "#ffa500" if val > 0.3 else "#00c87a"
                                    if "Specificity" in label:
                                        color = "#00c87a" if val > 0.5 else "#ff4b4b"
                                    st.markdown(f"""
                                    <div class="nlp-detail">
                                        <b>{label}</b> — {val:.2f}
                                        <div style="background:#2d3450;border-radius:4px;height:8px;margin-top:3px">
                                            <div style="width:{bar_pct}%;background:{color};height:8px;border-radius:4px"></div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                        with shap_col:
                            st.subheader("🔍 Key Risk Factors (Structured)")
                            factors = r.get("risk_factors", [])
                            if factors:
                                for f in factors:
                                    imp = f['impact']
                                    arrow = "🔺" if imp > 0 else "🔻"
                                    direction = "increases fraud risk" if imp > 0 else "reduces fraud risk"
                                    st.markdown(
                                        f"<div class='nlp-detail'>{arrow} <b>{f['feature']}</b> — "
                                        f"{direction} ({imp:+.3f})</div>",
                                        unsafe_allow_html=True,
                                    )
                            else:
                                st.info("No SHAP breakdown available.")

                        # ─── AI Interpretation ────────────────────────────────
                        st.divider()
                        st.subheader("🤖 AI Interpretation")
                        score = r['final_score']
                        if score >= 60:
                            st.error(
                                "⚠️ **HIGH RISK**: This claim exhibits strong indicators of potential fraud "
                                "across both structured data patterns and the claim narrative. "
                                "Recommend escalation and detailed manual review."
                            )
                        elif score >= 30:
                            st.warning(
                                "⚠️ **MEDIUM RISK**: The claim shows moderate irregularities. "
                                "Some signals are consistent with fraud patterns. "
                                "Further verification of documentation and witnesses is advised."
                            )
                        else:
                            st.success(
                                "✅ **LOW RISK**: This claim appears consistent with legitimate patterns. "
                                "Both structured data and narrative text align with expected legitimate claim language."
                            )

                else:
                    st.error(f"❌ API returned status {resp.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure FastAPI is running: `uvicorn src.api.main:app --reload`")
            except Exception as e:
                st.error(f"❌ Error: {e}")