import streamlit as st

# Hide Streamlit branding and padding for embedding
st.set_page_config(page_title="Blind System Comparison", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("Blind System Energy & Efficiency Comparison")
st.write("Use this tool to compare energy performance and cost savings between existing and new blind systems installed between glazing.")

# Section 1: Input Motor Power & Movement Data
st.header("1. Motor Energy Consumption")

motor_power_old = st.number_input("Motor Power - Existing System (W)", value=60)
motor_power_new = st.number_input("Motor Power - New System (W)", value=45)

movement_scenarios = {
    "Sunny Day (6 movements)": 6,
    "Partly Cloudy (12 movements)": 12,
    "Fully Cloudy (2 movements)": 2,
    "Custom": None
}

scenario = st.selectbox("Typical Movement Scenario", list(movement_scenarios.keys()))

if scenario == "Custom":
    movements_per_day = st.number_input("Custom Movements per Day (Full Cycles)", value=8)
else:
    movements_per_day = movement_scenarios[scenario]

days_operated_per_year = st.number_input("Days Operated per Year", value=260)

total_energy_old = (motor_power_old / 1000) * movements_per_day * days_operated_per_year
total_energy_new = (motor_power_new / 1000) * movements_per_day * days_operated_per_year

# Section 2: Thermal Performance
st.header("2. Thermal Performance")

solar_gain_existing = st.number_input("Solar Heat Gain Coefficient - Existing Blinds", value=0.12)
solar_gain_new = st.number_input("Solar Heat Gain Coefficient - New Blinds", value=0.06)
solar_radiation_summer = st.number_input("Average Solar Radiation (W/m²) - Summer", value=400)
window_area = st.number_input("Total Window Area (m²)", value=1000)
ac_cost_per_kwh = st.number_input("Electricity Cost for Cooling (£/kWh)", value=0.20)
ac_efficiency = st.number_input("Cooling System Efficiency (COP)", value=3.0)

solar_gain_diff = (solar_gain_existing - solar_gain_new) * solar_radiation_summer * window_area
cooling_energy_saved_kwh = solar_gain_diff * (1 / ac_efficiency) * (1 / 1000) * days_operated_per_year
cooling_cost_saved = cooling_energy_saved_kwh * ac_cost_per_kwh

# Winter performance
st.subheader("Heat Loss Reduction - Winter")

u_value_existing = st.number_input("U-Value - Existing System (W/m²K)", value=1.2)
u_value_new = st.number_input("U-Value - New System (W/m²K)", value=1.0)
indoor_temp = st.number_input("Indoor Temperature (°C)", value=21)
outdoor_temp_winter = st.number_input("Average Outdoor Temperature - Winter (°C)", value=5)
days_heating = st.number_input("Heating Days per Year", value=180)
heating_cost_per_kwh = st.number_input("Cost of Heating Energy (£/kWh)", value=0.10)

heat_loss_existing = u_value_existing * window_area * (indoor_temp - outdoor_temp_winter) * 24 * days_heating / 1000
heat_loss_new = u_value_new * window_area * (indoor_temp - outdoor_temp_winter) * 24 * days_heating / 1000
heat_saving_kwh = heat_loss_existing - heat_loss_new
heating_cost_saved = heat_saving_kwh * heating_cost_per_kwh

# Section 3: Results
st.header("3. Results & Comparison")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Existing System")
    st.metric("Motor Energy (kWh/year)", f"{total_energy_old:.1f}")
    st.metric("Total Heat Loss (kWh/year)", f"{heat_loss_existing:.1f}")
with col2:
    st.subheader("New System")
    st.metric("Motor Energy (kWh/year)", f"{total_energy_new:.1f}")
    st.metric("Total Heat Loss (kWh/year)", f"{heat_loss_new:.1f}")

st.subheader("Estimated Energy & Cost Savings")
st.write(f"**Cooling Energy Saved**: {cooling_energy_saved_kwh:.1f} kWh/year")
st.write(f"**Cooling Cost Saved**: £{cooling_cost_saved:.2f}/year")

st.write(f"**Heating Energy Saved**: {heat_saving_kwh:.1f} kWh/year")
st.write(f"**Heating Cost Saved**: £{heating_cost_saved:.2f}/year")

st.markdown("---")
st.caption("Edit any inputs to reflect specific project conditions. All values are annual estimates based on your assumptions.")
