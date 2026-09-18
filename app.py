import streamlit as st
import pandas as pd
import plotly.express as px
from engine import DataObject, LifecycleValuationEngine

st.set_page_config(page_title="Smart Data Lifecycle Manager", layout="wide", page_icon="💾")

st.title("💾 AI Smart Data Lifecycle Manager")
st.markdown("Evaluate enterprise data utility based on **semantic value, dependencies, and compliance** instead of blunt age.")

# User override memory
if "overrides" not in st.session_state:
    st.session_state.overrides = {}

# Sidebar sliders
st.sidebar.header("⚙️ Valuation Weights")
w_prob = st.sidebar.slider("Future Demand Weight", 10.0, 50.0, 35.0)
w_legal = st.sidebar.slider("Legal / Compliance Weight", 10.0, 50.0, 30.0)
w_dep = st.sidebar.slider("Dependency Lineage Weight", 10.0, 50.0, 25.0)
w_cost = st.sidebar.slider("Storage Cost Penalty", 1.0, 30.0, 10.0)

engine = LifecycleValuationEngine(w_prob, w_legal, w_dep, w_cost)

# Sample test files
sample_data = [
    DataObject("F-001", "2019_Master_Blueprint.dwg", 124.0, 2190, 2250, False, 32, False, 0.15),
    DataObject("F-002", "ci_build_cache_dup.tar", 4800.0, 380, 380, True, 0, False, 0.01),
    DataObject("F-003", "client_tax_records_2021.enc", 18.5, 920, 1200, False, 2, True, 0.05),
    DataObject("F-004", "q3_revenue_forecast.xlsx", 14.2, 4, 30, False, 8, False, 0.88),
    DataObject("F-005", "brand_design_assets.ai", 450.0, 1400, 1500, False, 14, False, 0.12),
    DataObject("F-006", "temp_screen_recording.mov", 1200.0, 280, 290, False, 0, False, 0.05)
]

# Run analysis
results = []
for item in sample_data:
    tier, score, reason = engine.evaluate(item)
    current_tier = st.session_state.overrides.get(item.file_id, tier)
    results.append({
        "File ID": item.file_id,
        "Filename": item.name,
        "Size (MB)": item.size_mb,
        "Days Idle": item.days_since_last_access,
        "Dependencies": item.dependency_count,
        "Legal Flag": item.is_legal_or_compliance,
        "AI Score": score,
        "Storage Tier": current_tier,
        "AI Explanation": reason
    })

df = pd.DataFrame(results)

# Top metrics
c1, c2, c3 = st.columns(3)
c1.metric("Total Files Tracked", len(df))
c2.metric("Total Storage Used", f"{df['Size (MB)'].sum() / 1024:.2f} GB")
quarantined = df[df["Storage Tier"] == "Deletion Candidate"]["Size (MB)"].sum() / 1024
c3.metric("Storage Saved via Quarantine", f"{quarantined:.2f} GB")

st.divider()

# Charts and tables
v1, v2 = st.columns([1, 2])
with v1:
    st.subheader("Tier Distribution")
    fig = px.pie(df, names="Storage Tier", color="Storage Tier",
                 color_discrete_map={
                     "Active": "#00CC96",
                     "Archived": "#636EFA",
                     "Deep Archive": "#AB63FA",
                     "Review": "#FFA15A",
                     "Deletion Candidate": "#EF553B"
                 })
    st.plotly_chart(fig, use_container_width=True)

with v2:
    st.subheader("Data Lifecycle Register")
    st.dataframe(df[["Filename", "Size (MB)", "Storage Tier", "AI Score", "AI Explanation"]], use_container_width=True)

st.divider()

# Review actions
st.subheader("🛡️ Safety Quarantine & Manual Review Queue")
for item in sample_data:
    tier, score, reason = engine.evaluate(item)
    current_tier = st.session_state.overrides.get(item.file_id, tier)
    if current_tier in ["Review", "Deletion Candidate"]:
        with st.expander(f"Action needed: {item.name} [{current_tier}]"):
            st.write(f"**AI Reasoning:** {reason}")
            b1, b2, b3 = st.columns(3)
            if b1.button("Approve AI Action", key=f"ok_{item.file_id}"):
                st.success(f"Confirmed {current_tier}")
            if b2.button("Override: Move to Deep Archive", key=f"arc_{item.file_id}"):
                st.session_state.overrides[item.file_id] = "Deep Archive"
                st.rerun()
            if b3.button("Override: Keep Active", key=f"act_{item.file_id}"):
                st.session_state.overrides[item.file_id] = "Active"
                st.rerun()
                