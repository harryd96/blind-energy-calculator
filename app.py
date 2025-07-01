import streamlit as st
from PIL import Image

# Page config and styling
st.set_page_config(page_title="Blind System Comparison", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    </style>
    """, unsafe_allow_html=True)

# Load and show logo (using relative path for Streamlit Cloud)
logo = Image.open("umbra_logo_white_rgb.png")
st.image(logo, width=300)

# Title
st.title("Blind System Energy & Efficiency Comparison")
st.write("Use this tool to compare energy performance and cost savings between existing and new blind systems installed between glazing.")

# Reset parameters button
if 'reset' not in st.session_state:
    st.session_state.reset = False

if st.button("🔄 Reset to Shard Baseline Parameters"):
    st.session_state.reset = True

# Baseline values from Shard documentation
default_values = {
    "motor_power_old": 120,
    "motor_power_new": 10,
    "standby_power": 0.5,
    "solar_gain_existing": 0.12,
    "u_value_existing": 1.2,
    "solar_gain_new": 0.12,
    "u_value_new": 1.2,
    "window_area": 44800,
    "solar_radiation_summer": 400,
    "ac_efficiency": 3.0,
    "ac_cost_per_kwh": 0.20,
    "indoor_temp": 21,
    "outdoor_temp_winter": 5,
    "days_heating": 180,
    "heating_cost_per_kwh": 0.10,
    "days_operated_per_year": 260,
    "movements_per_day": 6,
    "usage_factor_old": 0.8,
    "usage_factor_new": 1.0
}

# Layout Columns for Visual Comparison
left, right = st.columns(2)

with left:
    st.header("🚫 Existing System")
    motor_power_old = st.number_input("Motor Power (W) - Active", value=default_values["motor_power_old"] if st.session_state.reset else 120)
    usage_factor_old = st.slider("Estimated Usage (% Floors Active)", min_value=0.0, max_value=1.0, value=default_values["usage_factor_old"] if st.session_state.reset else 0.8)
    solar_gain_existing = st.number_input("Solar Heat Gain Coefficient", value=default_values["solar_gain_existing"] if st.session_state.reset else 0.12, key="sge")
    u_value_existing = st.number_input("U-Value (W/m²K)", value=default_values["u_value_existing"] if st.session_state.reset else 1.2, key="uve")

with right:
    st.header("✅ New System")
    motor_power_new = st.number_input("Motor Power (W) - Active", value=default_values["motor_power_new"] if st.session_state.reset else 10)
    usage_factor_new = st.slider("Estimated Usage (% Floors Active)", min_value=0.0, max_value=1.0, value=default_values["usage_factor_new"] if st.session_state.reset else 1.0)
    solar_gain_new = st.number_input("Solar Heat Gain Coefficient", value=default_values["solar_gain_new"] if st.session_state.reset else 0.06, key="sgn")
    u_value_new = st.number_input("U-Value (W/m²K)", value=default_values["u_value_new"] if st.session_state.reset else 1.0, key="uvn")

# Shared Inputs
st.markdown("---")
st.header("⚙️ System Use & Environmental Inputs")

movement_scenarios = {
    "Sunny Day (6 movements)": 6,
    "Partly Cloudy (12 movements)": 12,
    "Fully Cloudy (2 movements)": 2,
    "Custom": None
}
scenario = st.selectbox("Select Movement Scenario", list(movement_scenarios.keys()))
if scenario == "Custom":
    movements_per_day = st.number_input("Custom Movements/Day", value=default_values["movements_per_day"] if st.session_state.reset else 8)
else:
    movements_per_day = movement_scenarios[scenario]

days_operated_per_year = st.number_input("Days Operated per Year", value=default_values["days_operated_per_year"] if st.session_state.reset else 260)
window_area = st.number_input("Window Area (m²)", value=default_values["window_area"] if st.session_state.reset else 1000)
solar_radiation_summer = st.number_input("Solar Radiation Summer Avg (W/m²)", value=default_values["solar_radiation_summer"] if st.session_state.reset else 400)
ac_efficiency = st.number_input("AC Efficiency (COP)", value=default_values["ac_efficiency"] if st.session_state.reset else 3.0)
ac_cost_per_kwh = st.number_input("Cooling Electricity Cost (£/kWh)", value=default_values["ac_cost_per_kwh"] if st.session_state.reset else 0.20)
indoor_temp = st.number_input("Indoor Temp (°C)", value=default_values["indoor_temp"] if st.session_state.reset else 21)
outdoor_temp_winter = st.number_input("Winter Outdoor Temp (°C)", value=default_values["outdoor_temp_winter"] if st.session_state.reset else 5)
days_heating = st.number_input("Heating Days/Year", value=default_values["days_heating"] if st.session_state.reset else 180)
heating_cost_per_kwh = st.number_input("Heating Energy Cost (£/kWh)", value=default_values["heating_cost_per_kwh"] if st.session_state.reset else 0.10)
standby_power = default_values["standby_power"]

# Reset state flag after applying
st.session_state.reset = False

# Calculations (adjusted by usage and standby)
active_energy_old = (motor_power_old / 1000) * movements_per_day * days_operated_per_year * usage_factor_old
standby_energy_old = (standby_power / 1000) * 24 * days_operated_per_year * (1 - usage_factor_old)
motor_energy_old = active_energy_old + standby_energy_old

active_energy_new = (motor_power_new / 1000) * movements_per_day * days_operated_per_year * usage_factor_new
standby_energy_new = (standby_power / 1000) * 24 * days_operated_per_year * (1 - usage_factor_new)
motor_energy_new = active_energy_new + standby_energy_new

solar_gain_diff = (solar_gain_existing - solar_gain_new) * solar_radiation_summer * window_area
cooling_energy_saved_kwh = solar_gain_diff * (1 / ac_efficiency) * (1 / 1000) * days_operated_per_year
cooling_cost_saved = cooling_energy_saved_kwh * ac_cost_per_kwh

heat_loss_existing = u_value_existing * window_area * (indoor_temp - outdoor_temp_winter) * 24 * days_heating / 1000
heat_loss_new = u_value_new * window_area * (indoor_temp - outdoor_temp_winter) * 24 * days_heating / 1000
heat_saving_kwh = heat_loss_existing - heat_loss_new
heating_cost_saved = heat_saving_kwh * heating_cost_per_kwh

# Visual Results
st.markdown("---")
st.header("📊 Summary")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Existing System")
    st.metric("Motor Energy", f"{motor_energy_old:.1f} kWh/year")
    st.metric("Heat Loss", f"{heat_loss_existing:.1f} kWh/year")

with col2:
    st.subheader("New System")
    st.metric("Motor Energy", f"{motor_energy_new:.1f} kWh/year")
    st.metric("Heat Loss", f"{heat_loss_new:.1f} kWh/year")



motor_cost_old = motor_energy_old * ac_cost_per_kwh
motor_cost_new = motor_energy_new * ac_cost_per_kwh

with col1:
    st.metric("Motor Cost", f"£{motor_cost_old:.2f}/year")

with col2:
    st.metric("Motor Cost", f"£{motor_cost_new:.2f}/year")


st.write(f"**Cooling Energy Saved**: {cooling_energy_saved_kwh:.1f} kWh/year")
st.write(f"**Cooling Cost Saved**: £{cooling_cost_saved:.2f}/year")
st.write(f"**Heating Energy Saved**: {heat_saving_kwh:.1f} kWh/year")
st.write(f"**Heating Cost Saved**: £{heating_cost_saved:.2f}/year")

st.markdown("---")
st.caption("Edit any inputs to match real-world scenarios. Results are illustrative estimates only.")
