import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Trip Builder Impact Model", layout="wide")

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

default_data = pd.DataFrame({
    "Month": months,
    "Users": [16428, 21562, 19346, 21126, 21077, 51702, 70346, 48902, 17855, 7465, 10082, 15142],
    "Conversion %": [23.41, 13.40, 14.92, 22.38, 15.72, 23.31, 31.29, 37.80, 35.14, 18.90, 21.78, 23.96],
    "AOV": [149.38, 464.79, 449.92, 354.13, 728.17, 361.27, 272.91, 242.50, 203.12, 180.25, 220.83, 159.60]
})

st.title("Trip Builder Impact Model")
st.caption("Scenario-based model for estimating GMV impact from Trip Builder adoption.")

st.subheader("Monthly Baseline Inputs")
edited_df = st.data_editor(
    default_data,
    use_container_width=True,
    num_rows="fixed"
)

st.subheader("Scenario Assumptions")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    low_use = st.number_input("Low Trip Builder Use %", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
with col2:
    mid_use = st.number_input("Mid Trip Builder Use %", min_value=0.0, max_value=100.0, value=25.0, step=0.5)
with col3:
    high_use = st.number_input("High Trip Builder Use %", min_value=0.0, max_value=100.0, value=40.0, step=0.5)
with col4:
    tb_conversion_increase = st.number_input("TB Conversion % Increase", min_value=0.0, max_value=500.0, value=20.0, step=0.5)
with col5:
    tb_aov_increase = st.number_input("TB AOV % Increase", min_value=0.0, max_value=500.0, value=20.0, step=1.0)

def calculate_scenario(df, trip_builder_use_pct, tb_conversion_increase_pct, tb_aov_increase_pct):
    working = df.copy()

    working["Baseline Conversion"] = working["Conversion %"] / 100
    working["Trip Builder Use"] = trip_builder_use_pct / 100
    working["TB Conversion"] = working["Baseline Conversion"] * (1 + (tb_conversion_increase_pct / 100))
    working["TB AOV Multiplier"] = 1 + (tb_aov_increase_pct / 100)

    working["Baseline GMV"] = working["Users"] * working["Baseline Conversion"] * working["AOV"]

    working["TB Users"] = working["Users"] * working["Trip Builder Use"]
    working["Non-TB Users"] = working["Users"] * (1 - working["Trip Builder Use"])

    working["New GMV"] = (
        working["TB Users"] * working["TB Conversion"] * (working["AOV"] * working["TB AOV Multiplier"])
        + working["Non-TB Users"] * working["Baseline Conversion"] * working["AOV"]
    )

    total_baseline = working["Baseline GMV"].sum()
    total_new = working["New GMV"].sum()
    lift = total_new - total_baseline
    lift_pct = (lift / total_baseline * 100) if total_baseline else 0

    return {
        "monthly": working[["Month", "Baseline GMV", "New GMV"]].copy(),
        "baseline_gmv": total_baseline,
        "new_gmv": total_new,
        "lift": lift,
        "lift_pct": lift_pct
    }

low = calculate_scenario(edited_df, low_use, tb_conversion_increase, tb_aov_increase)
mid = calculate_scenario(edited_df, mid_use, tb_conversion_increase, tb_aov_increase)
high = calculate_scenario(edited_df, high_use, tb_conversion_increase, tb_aov_increase)

st.subheader("Scenario Summary")
c1, c2, c3 = st.columns(3)

def render_summary(col, label, scenario):
    with col:
        st.markdown(f"### {label}")
        st.metric("Baseline GMV", f"${scenario['baseline_gmv']:,.0f}")
        st.metric("New GMV", f"${scenario['new_gmv']:,.0f}")
        st.metric("Incremental GMV", f"${scenario['lift']:,.0f}")
        st.metric("% Lift", f"{scenario['lift_pct']:.2f}%")

render_summary(c1, "Low Scenario", low)
render_summary(c2, "Mid Scenario", mid)
render_summary(c3, "High Scenario", high)

st.subheader("Monthly GMV Comparison (Mid Scenario)")
chart_df = mid["monthly"].melt(
    id_vars="Month",
    value_vars=["Baseline GMV", "New GMV"],
    var_name="Scenario",
    value_name="GMV"
)

fig = px.bar(
    chart_df,
    x="Month",
    y="GMV",
    color="Scenario",
    barmode="group",
    title="Baseline vs Trip Builder GMV"
)
fig.update_layout(xaxis_title="", yaxis_title="GMV")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Monthly Detail (Mid Scenario)")
st.dataframe(mid["monthly"], use_container_width=True)