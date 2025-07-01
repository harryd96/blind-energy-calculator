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
    motor_power_old = st.number_input("Motor Power (W) - Active", help="Power consumed by the motor when moving the blinds.", value=default_values["motor_power_old"] if st.session_state.reset else 120)
    usage_factor_old = st.slider("Estimated Usage (% Floors Active)", help="Proportion of floors where automation is actively used.", min_value=0.0, max_value=1.0, value=default_values["usage_factor_old"] if st.session_state.reset else 0.8)
    solar_gain_existing = st.number_input("Solar Heat Gain Coefficient", help="Fraction of incoming solar radiation admitted through the blinds and glass.", value=default_values["solar_gain_existing"], key="sge")
    u_value_existing = st.number_input("U-Value (W/m²K)", help="Thermal transmittance indicating heat loss through the window system.", value=default_values["u_value_existing"], key="uve")

with right:
    st.header("✅ New System")
    motor_power_new = st.number_input("Motor Power (W) - Active", value=default_values["motor_power_new"] if st.session_state.reset else 10)
    usage_factor_new = st.slider("Estimated Usage (% Floors Active)", min_value=0.0, max_value=1.0, value=default_values["usage_factor_new"] if st.session_state.reset else 1.0)
    solar_gain_new = st.number_input("Solar Heat Gain Coefficient", value=default_values["solar_gain_new"], key="sgn")
    u_value_new = st.number_input("U-Value (W/m²K)", value=default_values["u_value_new"], key="uvn")

# Shared Inputs
st.markdown("---")
st.header("⚙️ System Use & Environmental Inputs")

movements_per_day = st.number_input("Blind Movements per Day", min_value=0, value=default_values["movements_per_day"] if st.session_state.reset else 6, help="Average full open-close cycles per day across the year.")

days_operated_per_year = st.number_input("Days Operated per Year", value=default_values["days_operated_per_year"] if st.session_state.reset else 260)
window_area = st.number_input("Window Area (m²)", help="Total glazed area under analysis, excluding floors not part of this study.", value=default_values["window_area"])
solar_radiation_summer = st.number_input("Solar Radiation Summer Avg (W/m²)", help="Average daily solar radiation expected on the facade during summer.", value=default_values["solar_radiation_summer"] if st.session_state.reset else 400)
ac_efficiency = st.number_input("AC Efficiency (COP)", help="Cooling system efficiency: ratio of cooling output to energy input.", value=default_values["ac_efficiency"] if st.session_state.reset else 3.0)
ac_cost_per_kwh = st.number_input("Cooling Electricity Cost (£/kWh)", help="Electricity cost per kWh for operating cooling systems.", value=default_values["ac_cost_per_kwh"] if st.session_state.reset else 0.20)
indoor_temp = st.number_input("Indoor Temp (°C)", help="Target indoor temperature during heating season.", value=default_values["indoor_temp"] if st.session_state.reset else 21)
outdoor_temp_winter = st.number_input("Winter Outdoor Temp (°C)", help="Average external temperature during heating season.", value=default_values["outdoor_temp_winter"] if st.session_state.reset else 5)
days_heating = st.number_input("Heating Days/Year", help="Estimated number of days when the building requires heating.", value=default_values["days_heating"] if st.session_state.reset else 180)
heating_cost_per_kwh = st.number_input("Heating Energy Cost (£/kWh)", help="Energy cost per kWh for heating provision.", value=default_values["heating_cost_per_kwh"] if st.session_state.reset else 0.10)
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

effective_solar_gain_old = solar_gain_existing * usage_factor_old
effective_solar_gain_new = solar_gain_new * usage_factor_new
solar_gain_diff = max((effective_solar_gain_old - effective_solar_gain_new) * solar_radiation_summer * window_area, 0)
cooling_energy_saved_kwh = solar_gain_diff * (1 / ac_efficiency) * (1 / 1000) * days_operated_per_year
cooling_cost_saved = cooling_energy_saved_kwh * ac_cost_per_kwh

effective_u_value_old = u_value_existing / usage_factor_old if usage_factor_old > 0 else u_value_existing
heat_loss_existing = effective_u_value_old * window_area * (indoor_temp - outdoor_temp_winter) * 24 * days_heating / 1000
effective_u_value_new = u_value_new / usage_factor_new if usage_factor_new > 0 else u_value_new
heat_loss_new = effective_u_value_new * window_area * (indoor_temp - outdoor_temp_winter) * 24 * days_heating / 1000
heat_saving_kwh = heat_loss_existing - heat_loss_new
heating_cost_saved = heat_saving_kwh * heating_cost_per_kwh

# Visual Results
st.markdown("---")
st.header("📊 Summary")

# Section 1: Motor Power and Costs
st.subheader("🔌 Motor Power Consumption and Running Costs")
motor_cost_old = motor_energy_old * ac_cost_per_kwh
motor_cost_new = motor_energy_new * ac_cost_per_kwh

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Existing System**")
    st.write(f"Motor Energy: **{motor_energy_old:.1f} kWh/year**")
    st.write(f"Motor Cost: **£{motor_cost_old:.2f}/year**")

with col2:
    st.markdown("**New System**")
    st.write(f"Motor Energy: **{motor_energy_new:.1f} kWh/year**")
    st.write(f"Motor Cost: **£{motor_cost_new:.2f}/year**")

# Section 2: Energy Efficiency Savings
st.subheader("🌡️ Energy Savings through Reduced Cooling and Heating")
col3, col4 = st.columns(2)
with col3:
    st.markdown("**Cooling Performance**")
    cooling_energy_old = effective_solar_gain_old * solar_radiation_summer * window_area * (1 / ac_efficiency) * (1 / 1000) * days_operated_per_year
    cooling_energy_new = effective_solar_gain_new * solar_radiation_summer * window_area * (1 / ac_efficiency) * (1 / 1000) * days_operated_per_year
    cooling_cost_old = cooling_energy_old * ac_cost_per_kwh
    cooling_cost_new = cooling_energy_new * ac_cost_per_kwh
    st.write(f"Existing System: {cooling_energy_old:.1f} kWh/year → £{cooling_cost_old:.2f}/year")
    st.write(f"New System: {cooling_energy_new:.1f} kWh/year → £{cooling_cost_new:.2f}/year")
    st.write(f"**Cooling Energy Saved**: {cooling_energy_saved_kwh:.1f} kWh/year")
    st.write(f"**Cooling Cost Saved**: £{cooling_cost_saved:.2f}/year")

with col4:
    st.markdown("**Heating Performance**")
    st.write(f"Existing System: {heat_loss_existing:.1f} kWh/year → £{heat_loss_existing * heating_cost_per_kwh:.2f}/year")
    st.write(f"New System: {heat_loss_new:.1f} kWh/year → £{heat_loss_new * heating_cost_per_kwh:.2f}/year")
    st.write(f"**Heating Energy Saved**: {heat_saving_kwh:.1f} kWh/year")
    st.write(f"**Heating Cost Saved**: £{heating_cost_saved:.2f}/year")


st.markdown("---")


# Clearer summary section
net_energy_savings = motor_energy_old - motor_energy_new + cooling_energy_saved_kwh + heat_saving_kwh
net_cost_savings = motor_cost_old - motor_cost_new + cooling_cost_saved + heating_cost_saved

st.markdown("### 💰 Total Annual Savings")
st.write(f"**Energy Savings**: {net_energy_savings:.1f} kWh/year")
st.write(f"**Cost Savings**: £{net_cost_savings:.2f}/year")

if net_cost_savings <= 0:
    st.info("The new system may not currently offer cost savings under the given assumptions. Consider revising usage, performance, or cost inputs.")
else:
    st.success("✅ The new system offers measurable savings through increased usage and/or improved efficiency.")

("Edit any inputs to match real-world scenarios. Results are illustrative estimates only.")
