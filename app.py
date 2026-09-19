import streamlit as st
import pandas as pd
import plotly.express as px
from engine import DataObject, LifecycleValuationEngine


# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Smart Data Lifecycle Manager",
    layout="wide",
    page_icon="💾"
)

st.title("💾 AI Smart Data Lifecycle Manager")

st.markdown(
    "Automated enterprise data valuation routing objects by "
    "**utility, graph dependencies, and compliance** instead of "
    "blunt Time-To-Live (TTL) policies."
)


# ---------------------------------------------------------
# Session State - Human Feedback / Overrides
# ---------------------------------------------------------
if "overrides" not in st.session_state:
    st.session_state.overrides = {}


# ---------------------------------------------------------
# Sidebar - Valuation Model Weights
# ---------------------------------------------------------
st.sidebar.header("⚙️ Valuation Model Weights")

w_prob = st.sidebar.slider(
    "Future Demand Weight",
    10.0,
    50.0,
    35.0,
    help="Weight given to predicted re-access frequency"
)

w_legal = st.sidebar.slider(
    "Legal / Compliance Weight",
    10.0,
    50.0,
    30.0,
    help="Weight given to statutory audit & retention requirements"
)

w_dep = st.sidebar.slider(
    "Dependency Lineage Weight",
    10.0,
    50.0,
    25.0,
    help="Weight given to connected files & downstream references"
)

w_cost = st.sidebar.slider(
    "Storage Cost Penalty",
    1.0,
    30.0,
    10.0,
    help="Penalty applied to large, expensive dormant files"
)

engine = LifecycleValuationEngine(
    w_prob,
    w_legal,
    w_dep,
    w_cost
)


# ---------------------------------------------------------
# Helper Function - Safely Convert CSV Values to Boolean
# ---------------------------------------------------------
def to_bool(value, default=False):
    """
    Safely convert CSV values such as:
    True, False, true, false, 1, 0, yes, no
    into Python booleans.
    """
    if pd.isna(value):
        return default

    if isinstance(value, bool):
        return value

    value = str(value).strip().lower()

    if value in {"true", "1", "yes", "y", "t"}:
        return True

    if value in {"false", "0", "no", "n", "f", ""}:
        return False

    return default


# ---------------------------------------------------------
# Data Source Selector
# ---------------------------------------------------------
st.sidebar.divider()
st.sidebar.header("📁 Data Source")

data_mode = st.sidebar.radio(
    "Choose Input:",
    ["Preset Enterprise Scenario", "Upload Custom CSV"]
)

raw_objects = []


# ---------------------------------------------------------
# Preset Enterprise Scenario
# ---------------------------------------------------------
if data_mode == "Preset Enterprise Scenario":

    raw_objects = [
        DataObject(
            "F-001",
            "2019_Master_Blueprint.dwg",
            124.0,
            2190,
            2250,
            False,
            32,
            False,
            0.15
        ),
        DataObject(
            "F-002",
            "ci_build_cache_dup.tar",
            4800.0,
            380,
            380,
            True,
            0,
            False,
            0.01
        ),
        DataObject(
            "F-003",
            "client_tax_records_2021.enc",
            18.5,
            920,
            1200,
            False,
            2,
            True,
            0.05
        ),
        DataObject(
            "F-004",
            "q3_revenue_forecast.xlsx",
            14.2,
            4,
            30,
            False,
            8,
            False,
            0.88
        ),
        DataObject(
            "F-005",
            "brand_design_assets.ai",
            450.0,
            1400,
            1500,
            False,
            14,
            False,
            0.12
        ),
        DataObject(
            "F-006",
            "temp_screen_recording.mov",
            1200.0,
            280,
            290,
            False,
            0,
            False,
            0.05
        ),
        DataObject(
            "F-007",
            "annual_audit_log_2020.json",
            65.0,
            1500,
            1550,
            False,
            5,
            True,
            0.02
        ),
        DataObject(
            "F-008",
            "legacy_db_dump_v1_dup.sql",
            8900.0,
            720,
            720,
            True,
            0,
            False,
            0.00
        )
    ]


# ---------------------------------------------------------
# Custom CSV Upload
# ---------------------------------------------------------
else:

    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV metadata",
        type=["csv"]
    )

    if uploaded_file is not None:

        try:
            user_df = pd.read_csv(uploaded_file)

            required_columns = [
                "file_id",
                "name",
                "size_mb",
                "days_since_last_access",
                "days_old",
                "is_duplicate",
                "dependency_count",
                "is_legal_or_compliance",
                "predicted_reaccess_prob"
            ]

            missing_columns = [
                column
                for column in required_columns
                if column not in user_df.columns
            ]

            if missing_columns:

                st.error(
                    "Your CSV is missing these required columns: "
                    + ", ".join(missing_columns)
                )

                st.info(
                    "Please use the required CSV structure shown below."
                )

            else:

                for index, row in user_df.iterrows():

                    try:

                        raw_objects.append(
                            DataObject(
                                file_id=str(row["file_id"]),
                                name=str(row["name"]),
                                size_mb=float(row["size_mb"]),
                                days_since_last_access=int(
                                    row["days_since_last_access"]
                                ),
                                days_old=int(row["days_old"]),
                                is_duplicate=to_bool(
                                    row["is_duplicate"]
                                ),
                                dependency_count=int(
                                    row["dependency_count"]
                                ),
                                is_legal_or_compliance=to_bool(
                                    row["is_legal_or_compliance"]
                                ),
                                predicted_reaccess_prob=float(
                                    row["predicted_reaccess_prob"]
                                )
                            )
                        )

                    except (ValueError, TypeError) as error:

                        st.error(
                            f"Invalid data in CSV row {index + 2}: {error}"
                        )

                        raw_objects = []
                        break

        except Exception as error:

            st.error(
                f"Could not read the CSV file: {error}"
            )

    else:

        st.info(
            "Upload a CSV file or switch to "
            "'Preset Enterprise Scenario' on the left."
        )


# ---------------------------------------------------------
# Process Data
# ---------------------------------------------------------
if raw_objects:

    results = []

    for item in raw_objects:

        tier, score, reason = engine.evaluate(item)

        current_tier = st.session_state.overrides.get(
            item.file_id,
            tier
        )

        results.append(
            {
                "File ID": item.file_id,
                "Filename": item.name,
                "Size (MB)": item.size_mb,
                "Days Idle": item.days_since_last_access,
                "Dependencies": item.dependency_count,
                "Legal Flag": item.is_legal_or_compliance,
                "AI Score (URI)": score,
                "Storage Tier": current_tier,
                "AI Explanation": reason
            }
        )

    df = pd.DataFrame(results)


    # -----------------------------------------------------
    # KPI Metrics
    # -----------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Objects",
        len(df)
    )

    c2.metric(
        "Total Volume",
        f"{df['Size (MB)'].sum() / 1024:.2f} GB"
    )

    quarantined = (
        df[df["Storage Tier"] == "Deletion Candidate"]["Size (MB)"].sum()
        / 1024
    )

    c3.metric(
        "Quarantine Savings",
        f"{quarantined:.2f} GB"
    )

    c4.metric(
        "Active Learning Overrides",
        len(st.session_state.overrides)
    )


    st.divider()


    # -----------------------------------------------------
    # Visualizations
    # -----------------------------------------------------
    v1, v2 = st.columns([1, 2])


    with v1:

        st.subheader("Storage Tier Allocation")

        fig = px.pie(
            df,
            names="Storage Tier",
            color="Storage Tier",
            color_discrete_map={
                "Active": "#00CC96",
                "Archived": "#636EFA",
                "Deep Archive": "#AB63FA",
                "Review": "#FFA15A",
                "Deletion Candidate": "#EF553B"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    with v2:

        st.subheader("Lifecycle Valuation Register")

        st.dataframe(
            df[
                [
                    "Filename",
                    "Size (MB)",
                    "Storage Tier",
                    "AI Score (URI)",
                    "AI Explanation"
                ]
            ],
            use_container_width=True
        )


        # -------------------------------------------------
        # Download CSV Report
        # -------------------------------------------------
        csv_data = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="📥 Export Valuation Report (CSV)",
            data=csv_data,
            file_name="storage_lifecycle_report.csv",
            mime="text/csv"
        )


    st.divider()


    # -----------------------------------------------------
    # Safety Quarantine & Review Queue
    # -----------------------------------------------------
    st.subheader("🛡️ Safety Quarantine & Review Queue")

    action_items = []

    for item in raw_objects:

        recommended_tier, _, _ = engine.evaluate(item)

        current_tier = st.session_state.overrides.get(
            item.file_id,
            recommended_tier
        )

        if current_tier in [
            "Review",
            "Deletion Candidate"
        ]:
            action_items.append(item)


    if not action_items:

        st.success(
            "No files currently require administrative review."
        )

    else:

        for item in action_items:

            tier, score, reason = engine.evaluate(item)

            current_tier = st.session_state.overrides.get(
                item.file_id,
                tier
            )

            with st.expander(
                f"Action Flag: {item.name} [{current_tier}]"
            ):

                st.write(
                    f"**AI Reasoning:** {reason}"
                )

                st.write(
                    f"**Size:** {item.size_mb} MB | "
                    f"**Idle Days:** {item.days_since_last_access} | "
                    f"**Dependencies:** {item.dependency_count}"
                )


                b1, b2, b3 = st.columns(3)


                if b1.button(
                    "Approve AI Recommendation",
                    key=f"app_{item.file_id}"
                ):

                    st.success(
                        f"Action confirmed for {item.name}"
                    )


                if b2.button(
                    "Override: Move to Deep Archive",
                    key=f"arc_{item.file_id}"
                ):

                    st.session_state.overrides[
                        item.file_id
                    ] = "Deep Archive"

                    st.rerun()


                if b3.button(
                    "Override: Keep Active",
                    key=f"act_{item.file_id}"
                ):

                    st.session_state.overrides[
                        item.file_id
                    ] = "Active"

                    st.rerun()