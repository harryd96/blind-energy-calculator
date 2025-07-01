# app.py – Umbra Blind Energy Model (stable release)
# -----------------------------------------------------------
#   Whole‑Year Blind Energy Impact for The Shard, London
#   Brand palette:  Bronze #7B7662  ·  Taupe #C7BB9B
#   Climate data:   St James’s Park TMY (monthly GHI & HDD)
#   Author:         ChatGPT assist (2025‑07‑01)
# -----------------------------------------------------------

import streamlit as st
import pandas as pd
from PIL import Image

# ───────────────────── Display Config & Brand CSS ─────────────────────
st.set_page_config(
    page_title="Shard Blind Energy",
    layout="wide",
    page_icon="💡",
    initial_sidebar_state="expanded"
)

BRAND_CSS = """
<style>
/* —— Umbra Light Theme —— */
html, body, .stApp, .css-18e3th9 {background:#ffffff; color:#000000;}
/* light grey sidebar background */
.css-1d391kg {background:#f7f7f7 !important;}
/* keep left pane scrollbar track light */
.css-1d391kg::-webkit-scrollbar-track {background:#f7f7f7;}

h1,h2,h3 {color:var(--bronze); font-weight:700;}
label, .stSlider>label {color:var(--bronze);}  /* sidebar labels */

/* Table styling */
thead {
  background-color:var(--bronze)!important;
  color:#ffffff!important;
  font-weight:600;
}
tbody tr:nth-child(even) {background:var(--row-alt);}  /* subtle alt rows */
table {border:1px solid var(--taupe);} 
td, th {padding:6px 10px;}

/* Numerical cells right‑aligned */
td:nth-child(2), td:nth-child(3), td:nth-child(4){text-align:right;}

/* Alert boxes */
.stAlert.success{background:#f0f9f2; border-left:6px solid var(--bronze);} 
.stAlert.warning{background:#fffbe8; border-left:6px solid var(--taupe);} 
</style>
"""

st.markdown(BRAND_CSS, unsafe_allow_html=True)

# ───────────────────── Logo & Title ─────────────────────
try:
    logo = Image.open("umbra_logo_white_rgb.png")
    st.image(logo, width=240)
except Exception:
    st.write("<b>UMBRA&</b>", unsafe_allow_html=True)

st.title("Blind System – Whole‑Year Energy Impact (London)")

# ───────────────────── Climate Data (monthly) ─────────────────────
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
GHI =  [24, 43, 75,105,132,140,145,135,100, 64, 35, 23]  # kWh/m²·mo (St James’s Park)
HDD =  [300,255,205,115, 55, 18, 11, 25, 80,165,240,290]  # °C·day / mo (base 18 °C)
irradiance = pd.Series(GHI, index=MONTHS)
hdd        = pd.Series(HDD, index=MONTHS)

# ───────────────────── Default Parameters ─────────────────────
DEFAULT = dict(
    area=44_800,               # m² glazed
    motor_old=120, motor_new=10,
    standby=0.5,
    moves=6,
    blinds=1000,
    days=260,
    usage_old=0.80, usage_new=1.00,
    shgc=0.12, shade_eff=0.90,
    u_glass=1.2, delta_u=0.15,
    cop=3.0,
    c_ele=0.20,  # £/kWh electricity
    c_heat=0.10, # £/kWh heating
)

# ───────────────────── Sidebar Inputs ─────────────────────
with st.sidebar:
    st.header("Model Inputs")
    area = st.number_input("Window Area (m²)", value=DEFAULT['area'],
                           help="Total glazed area analysed (hotel floors excluded).")

    st.subheader("Blind Usage (fraction of beneficial hours closed)")
    usage_old = st.slider("Existing system", 0.0, 1.0, DEFAULT['usage_old'], 0.05,
                          help="Fraction of time legacy blinds are closed when beneficial.")
    usage_new = st.slider("New system",      0.0, 1.0, DEFAULT['usage_new'], 0.05,
                          help="Expected utilisation rate of new blinds.")

    st.subheader("Motor & Movements")
    motor_old = st.number_input("Motor Power – OLD (W)", 1, 500, DEFAULT['motor_old'],
                               help="Active draw of one legacy motor while moving.")
    motor_new = st.number_input("Motor Power – NEW (W)", 1, 500, DEFAULT['motor_new'],
                               help="Active draw of one new motor while moving.")
    standby   = st.number_input("Stand‑by Power (W)", 0.0, 5.0, DEFAULT['standby'], 0.1,
                               help="Idle draw per motor when blinds not moving.")
    moves_day = st.number_input("Movements per blind per day", 0, 20, DEFAULT['moves'],
                               help="Average full‑travel cycles each blind performs daily.")
    n_blinds  = st.number_input("Quantity of blinds", 1, 10_000, DEFAULT['blinds'],
                               help="Total motorised blinds in scope.")

    st.subheader("Thermal & Economic")
    shgc = st.number_input("Fabric SHGC", 0.05, 0.9, DEFAULT['shgc'], 0.01,
                           help="Solar‑heat‑gain coefficient of blind fabric.")
    shade_eff = st.slider("Shade effectiveness", 0.0, 1.0, DEFAULT['shade_eff'], 0.05,
                          help="Fraction of incident solar blocked when blind is closed.")
    u_glass = st.number_input("Bare glass U (W/m²K)", 0.5, 3.0, DEFAULT['u_glass'], 0.05,
                             help="Thermal transmittance of glazing alone.")
    delta_u = st.number_input("ΔU with blind closed", 0.0, 0.5, DEFAULT['delta_u'], 0.01,
                             help="U‑value reduction when blind deployed.")
    cop = st.number_input("Cooling COP", 1.0, 6.0, DEFAULT['cop'], 0.1,
                          help="Coefficient of performance of cooling plant.")
    c_ele = st.number_input("Electricity £/kWh", 0.05, 0.50, DEFAULT['c_ele'], 0.01,
                           help="Tariff for electricity (motors & cooling).")
    c_heat = st.number_input("Heating £/kWh", 0.03, 0.30, DEFAULT['c_heat'], 0.01,
                            help="Tariff for heating (gas or district heat).")

# ───────────────────── Helper Functions ─────────────────────

def motor_kwh(active_W: float, standby_W: float, usage: float, moves: int, days: int, n: int) -> float:
    """Return annual kWh for n blinds."""
    active_hours = moves * 0.01  # assume 1 cycle = 36 s
    kwh_per_motor = ((active_W * active_hours * days * usage) +
                      (standby_W * (24 - active_hours) * days * (1 - usage))) / 1000
    return kwh_per_motor * n

fmt = lambda x: f"{x:,.2f}"
cur = lambda x: f"£{x:,.2f}"

# ───────────────────── Annual Cooling & Heating Loads ─────────────────────
solar_gain_old = shgc * (1 - usage_old * shade_eff) * irradiance * area  # kWh/mo
solar_gain_new = shgc * (1 - usage_new * shade_eff) * irradiance * area
cool_old = (solar_gain_old / cop).sum()
cool_new = (solar_gain_new / cop).sum()

U_old = u_glass - usage_old * delta_u
U_new = u_glass - usage_new * delta_u
heat_old = (U_old * area * hdd * 24 / 1000).sum()
heat_new = (U_new * area * hdd * 24 / 1000).sum()

# Motor kWh & Costs
motor_old_kwh = motor_kwh(motor_old, standby, usage_old, moves_day, DEFAULT['days'], n_blinds)
motor_new_kwh = motor_kwh(motor_new, standby, usage_new, moves_day, DEFAULT['days'], n_blinds)

cost_motor_old = motor_old_kwh * c_ele
cost_motor_new = motor_new_kwh * c_ele
cost_cool_old  = cool_old * c_ele
cost_cool_new  = cool_new * c_ele
cost_heat_old  = heat_old * c_heat
cost_heat_new  = heat_new * c_heat

# ───────────────────── Outputs ─────────────────────
st.header("📊 Results & Savings")

st.subheader("Motor Consumption ⚡")

motor_df = pd.DataFrame(
    {
        "Existing": [fmt(motor_old_kwh), cur(cost_motor_old)],
        "New":      [fmt(motor_new_kwh),  cur(cost_motor_new)],
        "Savings":  [fmt(motor_old_kwh - motor_new_kwh), cur(cost_motor_old - cost_motor_new)],
    },
    index=["kWh / yr", "£ / yr"],
)

st.table(motor_df)

# ────────── Cooling & Heating Table ──────────
st.subheader("Thermal Performance 🏢")
thermal_df = pd.DataFrame(
    {
        "Existing": [fmt(cool_old),  cur(cost_cool_old),  fmt(heat_old),  cur(cost_heat_old)],
        "New":      [fmt(cool_new),  cur(cost_cool_new),  fmt(heat_new),  cur(cost_heat_new)],
        "Savings":  [fmt(cool_old - cool_new), cur(cost_cool_old - cost_cool_new),
                      fmt(heat_old - heat_new), cur(cost_heat_old - cost_heat_new)],
    },
    index=["Cooling kWh / yr", "Cooling £ / yr", "Heating kWh / yr", "Heating £ / yr"],
)

st.table(thermal_df)

# ────────── Totals ──────────
energy_saved = (motor_old_kwh - motor_new_kwh) + (cool_old - cool_new) + (heat_old - heat_new)
cost_saved   = (cost_motor_old - cost_motor_new) + (cost_cool_old - cost_cool_new) + (cost_heat_old - cost_heat_new)

st.markdown(f"### 💰 **Total Annual Energy Saved:** {fmt(energy_saved)} kWh")
st.markdown(f"### 💰 **Total Annual Cost Saved:** {cur(cost_saved)}")

if cost_saved > 0:
    st.success("New system delivers annual cost savings under current assumptions.")
else:
    st.warning("New system increases annual cost. Adjust inputs or usage assumptions.")

st.caption("Monthly GHI & HDD source: London St James’s Park TMY · All £ & kWh rounded to two decimals.")
