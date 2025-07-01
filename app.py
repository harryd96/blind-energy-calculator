# app.py – Umbra Blind Energy Model (carbon‑aware release)
# -----------------------------------------------------------
#   Whole‑Year Blind Energy Impact for The Shard, London
#   CO₂‑equivalent & “trees‑saved / flights‑avoided” visual.
# -----------------------------------------------------------

import streamlit as st
import pandas as pd
from PIL import Image

# ───────────────────── Display Config ─────────────────────
st.set_page_config(
    page_title="Shard Blind Energy",
    layout="wide",
    page_icon="💡",
    initial_sidebar_state="expanded",
)

BRAND_CSS = """
<style>
:root {
  --bronze:#7b7662;
  --taupe:#c7bb9b;
  --row-alt:#2a2a2a;
}
html, body, .stApp {background:#0e0e0e; color:#ffffff;}
h1, h2, h3 {color:var(--bronze);} 

table {border:1px solid var(--taupe);} 
thead {background-color:var(--bronze)!important; color:#ffffff!important; font-weight:600;}
tbody tr:nth-child(even){background:var(--row-alt);} 
td, th {padding:6px 10px;}
td:nth-child(2), td:nth-child(3), td:nth-child(4){text-align:right;}

.stAlert.success {background:#143d1d; border-left:6px solid var(--bronze);} 
.stAlert.warning {background:#3d3614; border-left:6px solid var(--taupe);}  
</style>
"""

st.markdown(BRAND_CSS, unsafe_allow_html=True)

# ───────────────────── Logo & Title ─────────────────────
try:
    st.image(Image.open("umbra_logo_white_rgb.png"), width=240)
except Exception:
    st.write("<b>UMBRA&</b>", unsafe_allow_html=True)

st.title("Blind System – Whole‑Year Energy Impact (London)")

# ───────────────────── Climate Data (monthly) ─────────────────────
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
GHI  = [24,43,75,105,132,140,145,135,100,64,35,23]   # kWh/m²·month (St James’s Park TMY)
HDD  = [300,255,205,115,55,18,11,25,80,165,240,290]  # °C·day / month (base 18 °C)
irradiance = pd.Series(GHI, index=MONTHS)
hdd        = pd.Series(HDD, index=MONTHS)

# ───────────────────── Defaults & Constants ─────────────────────
DEFAULT = dict(
    area=44_800,
    motor_old=120, motor_new=10, standby=0.5, moves=6,
    blinds=1000, days=260,
    usage_old=0.80, usage_new=1.00,
    shade_eff=0.90, u_glass=1.2, delta_u=0.15,
    cop=3.0,
    c_ele=0.20, c_heat=0.10,
)

SHGC_OLD = 0.45  # Hexel Screen Vision 5 %
NEW_FABRICS = {
    "Umbra Alu‑Back Screen – SHGC 0.27": 0.27,
    "Umbra White‑Back Screen – SHGC 0.34": 0.34,
    "Umbra Standard Screen – SHGC 0.45": 0.45,
}

# Carbon factors & equivalences
ELEC_CO2 = 0.233  # kg CO₂/kWh (UK grid avg 2024)
HEAT_CO2 = 0.184  # kg CO₂/kWh (natural gas)
TREE_CO2 = 22      # kg CO₂ absorbed per mature tree per year
FLIGHT_CO2 = 1.6   # t CO₂ for one London–NYC return flight (economy seat)

# ───────────────────── Sidebar Inputs ─────────────────────
with st.sidebar:
    st.header("Model Inputs")
    area = st.number_input("Window Area (m²)", value=DEFAULT["area"], help="Total glazed curtain‑wall area (hotel floors excluded).")

    st.subheader("Blind Usage (fraction of beneficial hours closed)")
    usage_old = st.slider("Existing system", 0.0, 1.0, DEFAULT["usage_old"], 0.05)
    usage_new = st.slider("New system",      0.0, 1.0, DEFAULT["usage_new"], 0.05)

    st.subheader("Motor & Movements")
    motor_old = st.number_input("Motor Power – OLD (W)", 1, 500, DEFAULT["motor_old"])
    motor_new = st.number_input("Motor Power – NEW (W)", 1, 500, DEFAULT["motor_new"])
    standby   = st.number_input("Stand‑by Power (W)", 0.0, 5.0, DEFAULT["standby"], 0.1)
    moves_day = st.number_input("Movements per blind per day", 0, 20, DEFAULT["moves"])
    n_blinds  = st.number_input("Quantity of blinds", 1, 10_000, DEFAULT["blinds"])

    st.subheader("Fabric Selection")
    st.markdown(f"**Existing blinds:** Hexel Screen Vision 5 % (SHGC {SHGC_OLD})")
    shgc_new = NEW_FABRICS[st.selectbox("New blind fabric", list(NEW_FABRICS.keys()))]

    st.subheader("Thermal & Economic")
    shade_eff = st.slider("Shade effectiveness", 0.0, 1.0, DEFAULT["shade_eff"], 0.05)
    u_glass = st.number_input("Bare glass U (W/m²K)", 0.5, 3.0, DEFAULT["u_glass"], 0.05)
    delta_u = st.number_input("ΔU with blind closed", 0.0, 0.5, DEFAULT["delta_u"], 0.01)
    cop = st.number_input("Cooling COP", 1.0, 6.0, DEFAULT["cop"], 0.1)
    c_ele = st.number_input("Electricity £/kWh", 0.05, 0.50, DEFAULT["c_ele"], 0.01)
    c_heat = st.number_input("Heating £/kWh", 0.03, 0.30, DEFAULT["c_heat"], 0.01)

# ───────────────────── Helper Functions ─────────────────────

def motor_kwh(active_W: float, standby_W: float, usage: float, moves: int, days: int, n: int) -> float:
    """Return annual motor kWh for n blinds."""
    active_h = moves * 0.01  # one cycle ≈36 s
    kwh = ((active_W * active_h * days * usage) + (standby_W * (24 - active_h) * days * (1 - usage))) / 1000
    return kwh * n

fmt = lambda x: f"{x:,.2f}"
cur = lambda x: f"£{x:,.2f}"

# ───────────────────── Annual Loads & Costs ─────────────────────
solar_gain_old = SHGC_OLD * (1 - usage_old * shade_eff) * irradiance * area
solar_gain_new = shgc_new * (1 - usage_new * shade_eff) * irradiance * area
cool_old = (solar_gain_old / cop).sum()
cool_new = (solar_gain_new / cop).sum()

U_old = u_glass - usage_old * delta_u
U_new = u_glass - usage_new * delta_u
heat_old = (U_old * area * hdd * 24 / 1000).sum()
heat_new = (U_new * area * hdd * 24 / 1000).sum()

motor_old_kwh = motor_kwh(motor_old, standby, usage_old, moves_day, DEFAULT["days"], n_blinds)
motor_new_kwh = motor_kwh(motor_new, standby, usage_new, moves_day, DEFAULT["days"], n_blinds)

cost_motor_old, cost_motor_new = motor_old_kwh * c_ele, motor_new_kwh * c_ele
cost_cool_old,  cost_cool_new  = cool_old * c_ele,   cool_new * c_ele
cost_heat_old,  cost_heat_new  = heat_old * c_heat,  heat_new * c_heat

# ───────────────────── Carbon Savings ─────────────────────
co2_elec_saved = (motor_old_kwh - motor_new_kwh + cool_old - cool_new) * ELEC_CO2  # kg
co2_heat_saved = (heat_old - heat_new) * HEAT_CO2                                   # kg
co2_total_kg   = co2_elec_saved + co2_heat_saved
co2_total_t    = co2_total_kg / 1000
TREES_EQ       = int(round(co2_total_kg / TREE_CO2))
FLIGHTS_EQ     = int(round(co2_total_t / FLIGHT_CO2))

# ───────────────────── Outputs ─────────────────────
st.header("📊 Results & Savings")

# Motor consumption table
st.subheader("Motor Consumption ⚡")
_st_motor = pd.DataFrame({
    "Existing": [fmt(motor_old_kwh), cur(cost_motor_old)],
    "New":      [fmt(motor_new_kwh), cur(cost_motor_new)],
    "Savings":  [fmt(motor_old_kwh - motor_new_kwh), cur(cost_motor_old - cost_motor_new)],
}, index=["kWh / yr", "£ / yr"])
st.table(_st_motor)

# Thermal performance table
st.subheader("Thermal Performance 🏢")
_st_therm = pd.DataFrame({
    "Existing": [fmt(cool_old), cur(cost_cool_old), fmt(heat_old), cur(cost_heat_old)],
