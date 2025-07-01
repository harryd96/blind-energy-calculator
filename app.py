import streamlit as st
import pandas as pd
from math import ceil
from PIL import Image

# ──────────────────────────────────────────────────────────────
#  Umbra – Rigorous Annual Facade‑Blind Energy Model (London)
#  Re‑written 2025‑07‑01  ─ All calculations now use monthly
#  Typical Meteorological Year (TMY) data for London Heathrow.
#  Cooling = solar only, Heating = conduction only (ΔU method).
# ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Shard Blind Energy Model", layout="wide")

# ────────── Styling & Branding ──────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1rem; padding-bottom: 1rem;}

:root {
  --bronze: #7b7662;
  --taupe: #c7bb9b;
  --umbra-black: #000000;
  --umbra-white: #ffffff;
}

h1, h2, h3 {color: var(--bronze);}

.css-1d391kg, .stSlider > label, .sidebar-content label {color: var(--bronze);}

thead {background-color: var(--taupe) !important; color: var(--umbra-black) !important; font-weight:600;}
tbody tr:nth-child(even) {background-color: #f5f5f5;}

.stAlert.success {background-color: #e8f5e9; border-left: 6px solid var(--bronze);}
.stAlert.warning {background-color: #fffbe5; border-left: 6px solid var(--taupe);}
</style>
""", unsafe_allow_html=True)
logo = Image.open("umbra_logo_white_rgb.png")
st.image(logo, width=260)

st.title("Blind System – Whole‑Year Energy Impact (London)")

# ────────── Constants & TMY Data ──────────
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
# Monthly global horizontal irradiation kWh/m² (TMY **London St James’s Park**, WMO 03770)
GHI = [24, 43, 75, 105, 132, 140, 145, 135, 100, 64, 35, 23]
# Monthly heating‑degree days base‑18 °C (°C·day) – St James’s Park
HDD = [300, 255, 205, 115, 55, 18, 11, 25, 80, 165, 240, 290]
HOURS_PER_MONTH = [31*24,28*24,31*24,30*24,31*24,30*24,31*24,31*24,30*24,31*24,30*24,31*24]

# convert lists to series for vector ops
irradiance = pd.Series(GHI, index=MONTHS)       # kWh/m²·month
hdd = pd.Series(HDD, index=MONTHS)               # °C·day / mo
hours = pd.Series(HOURS_PER_MONTH, index=MONTHS) # hours per month

# ────────── Default Parameters (Shard) ──────────
DEFAULT = {
    "window_area": 44_800,          # m² (Shard minus Shangri‑La)
    "motor_power_old": 120, "motor_power_new": 10,  # W active
    "standby": 0.5,                 # W standby
    "movements_day": 6,
    "num_blinds": 1000,
    "days_year": 260,
    "usage_old": 0.80, "usage_new": 1.00,
    "shgc": 0.12,                   # both fabrics
    "shade_eff": 0.90,              # % of solar blocked when blind engaged
    "u_glass": 1.2,                 # W/m²K without blind
    "delta_u": 0.15,                # U‑value reduction when blind closed
    "ac_cop": 3.0,
    "cool_cost": 0.20, "heat_cost": 0.10,
    "setpoint_heat": 21,            # °C
}

# ────────── Sidebar Inputs ──────────
with st.sidebar:
    st.header("Model Inputs")
    area = st.number_input("Window Area (m²)", value=DEFAULT["window_area"], help="Total glazed area considered in the energy model."DEFAULT["window_area"])
    st.subheader("Blind Usage (share of time closed when beneficial)")
    usage_old = st.slider("Existing system", 0.0, 1.0, DEFAULT["usage_old"], 0.05, help="Percentage of time existing blinds are closed when they should be shading or insulating.")
    usage_new = st.slider("New system", 0.0, 1.0, DEFAULT["usage_new"], 0.05, help="Expected utilisation rate for the new blind system (1 = always used optimally).")

    st.subheader("Motor & Movements")
    active_old = st.number_input("Motor Power OLD (W)", 1, 500, DEFAULT["motor_power_old"], help="Power drawn by one existing motor while moving.")
    active_new = st.number_input("Motor Power NEW (W)", 1, 500, DEFAULT["motor_power_new"], help="Power drawn by one replacement motor while moving.")
    standby = st.number_input("Stand‑by Power (W)", 0.0, 5.0, DEFAULT["standby"], 0.1, help="Idle power for one motor when blinds are not moving.")
    moves = st.number_input("Movements per day", 0, 20, DEFAULT["movements_day"], help="Average full‑travel cycles each blind makes per day.")
    num_blinds = st.number_input("Quantity of blinds", 1, 10000, DEFAULT["num_blinds"], help="Total number of motorised blinds in scope.")

    st.subheader("Thermal & Economic")
    shgc = st.number_input("SHGC of fabric", 0.05, 0.9, DEFAULT["shgc"], 0.01, help="Solar Heat Gain Coefficient of the blind fabric alone.")
    shade_eff = st.slider("Shade effectiveness (blocks % solar)", 0.0, 1.0, DEFAULT["shade_eff"], 0.05, help="Proportion of solar radiation blocked when a blind is closed.")
    u_glass = st.number_input("Bare Glass U (W/m²K)", 0.5, 3.0, DEFAULT["u_glass"], 0.05, help="Thermal transmittance of the facade glazing alone.")
    delta_u = st.number_input("ΔU when blind closed", 0.0, 0.5, DEFAULT["delta_u"], 0.01, help="U‑value reduction achieved when blind is fully closed.")
    cop = st.number_input("Cooling COP", 1.0, 6.0, DEFAULT["ac_cop"], 0.1, help="Coefficient of Performance of the cooling plant (higher = more efficient).")
    cost_cool = st.number_input("Electricity £/kWh (AC & motor)", 0.05, 0.5, DEFAULT["cool_cost"], 0.01, help="Unit electricity cost used for both cooling and motor energy.")
    cost_heat = st.number_input("Fuel £/kWh (heating)", 0.03, 0.3, DEFAULT["heat_cost"], 0.01, help="Fuel or district‑heat tariff applied to heating load.")

# ────────── Helper Functions ──────────

def motor_energy(active_W: float, standby_W: float, usage: float, moves_per_day: int, days: int, n_blinds: int) -> float:
    active_hours = moves_per_day * 0.01   # assume 1 cycle ≈ 1 % of an hour (36 s)
    return ((active_W*active_hours*days*usage) + (standby_W*(24-active_hours)*days*(1-usage))) / 1000 * n_blinds

# ────────── Cooling Calculation (monthly) ──────────
shaded_gain_old = shgc * (1 - usage_old*shade_eff) * irradiance * area  # kWh/mo admitted
shaded_gain_new = shgc * (1 - usage_new*shade_eff) * irradiance * area
# Convert solar gain to cooling load (divide by COP)
cool_load_old = (shaded_gain_old / cop).sum()
cool_load_new = (shaded_gain_new / cop).sum()

# ────────── Heating Calculation (monthly) ──────────
U_old_eff = u_glass - usage_old*delta_u
U_new_eff = u_glass - usage_new*delta_u
heat_load_old = (U_old_eff * area * hdd * 24 / 1000).sum()  # kWh/yr
heat_load_new = (U_new_eff * area * hdd * 24 / 1000).sum()

# ────────── Motor kWh ──────────
motor_kwh_old = motor_energy(active_old, standby, usage_old, moves, DEFAULT["days_year"], num_blinds)
motor_kwh_new = motor_energy(active_new, standby, usage_new, moves, DEFAULT["days_year"], num_blinds)

# ────────── Costs ──────────
cost_motor_old = motor_kwh_old * cost_cool
cost_motor_new = motor_kwh_new * cost_cool
cost_cool_old = cool_load_old * cost_cool
cost_cool_new = cool_load_new * cost_cool
cost_heat_old = heat_load_old * cost_heat
cost_heat_new = heat_load_new * cost_heat

# ────────── Output Tables ──────────
st.markdown("## 📊 Results & Savings")

# Motor table
# Format numbers to 2 dp
fmt = lambda x: f"{x:,.2f}"
£fmt = lambda x: f"£{x:,.2f}"

motor_df = pd.DataFrame({
    "Existing": [fmt(motor_kwh_old), £fmt(cost_motor_old)],
    "New":      [fmt(motor_kwh_new),  £fmt(cost_motor_new)],
    "Savings":  [fmt(motor_kwh_old-motor_kwh_new), £fmt(cost_motor_old-cost_motor_new)],
}, index=["Motor kWh/y", "Motor £/y"])

st.subheader("Motor Consumption ⚡"))
st.table(motor_df)

# Cooling & Heating table
therm_df = pd.DataFrame({
    "Existing": [fmt(cool_load_old), £fmt(cost_cool_old), fmt(heat_load_old), £fmt(cost_heat_old)],
    "New":      [fmt(cool_load_new), £fmt(cost_cool_new), fmt(heat_load_new), £fmt(cost_heat_new)],
    "Savings":  [fmt(cool_load_old-cool_load_new), £fmt(cost_cool_old-cost_cool_new),
                  fmt(heat_load_old-heat_load_new), £fmt(cost_heat_old-cost_heat_new)],
}, index=["Cooling kWh/y","Cooling £/y","Heating kWh/y","Heating £/y"])

st.subheader("Thermal Performance 🏢"))
st.table(therm_df)

# Totals
energy_saved = (motor_kwh_old-motor_kwh_new)+(cool_load_old-cool_load_new)+(heat_load_old-heat_load_new)
cost_saved = (cost_motor_old-cost_motor_new)+(cost_cool_old-cost_cool_new)+(cost_heat_old-cost_heat_new)

st.markdown(f"### 💰 **Total Annual Energy Saved:** {energy_saved:,.2f} kWh/year")
st.markdown(f"### 💰 **Total Annual Cost Saved:** £{cost_saved:,.2f}/year")


if cost_saved > 0:
    st.success("New system delivers annual cost savings under current assumptions.")
else:
    st.warning("New system increases annual cost. Adjust inputs or usage assumptions.")

st.caption("All monthly irradiance & HDD values = **London St James’s Park TMY** (central‑London climate station). Shade effectiveness = proportion of solar blocked when blinds engaged. Adjust in sidebar for scenario analysis.")
