# app.py – Umbra Blind Energy Model (clean)
import streamlit as st
import pandas as pd
from PIL import Image

"""
Whole‑Year Blind Energy Model for The Shard (London)
Brand colours – Bronze #7B7662 · Taupe #C7BB9B
Climate data – London St James’s Park TMY (monthly GHI & HDD)
"""

# ───────────────────────────────────────── Display Config
st.set_page_config(page_title="Shard Blind Energy", layout="wide")

st.markdown(
    """
    <style>
    #MainMenu, header, footer {visibility:hidden;}
    .block-container {padding-top:1rem; padding-bottom:1rem;}
    :root {--bronze:#7b7662; --taupe:#c7bb9b; --umbra-black:#000000;}
    h1,h2,h3 {color:var(--bronze);}              /* headings */
    label, .stSlider>label {color:var(--bronze);} /* sidebar */
    thead {background-color:var(--taupe)!important; color:var(--umbra-black)!important; font-weight:600;}
    tbody tr:nth-child(even){background:#f5f5f5;}
    .stAlert.success{background:#e8f5e9; border-left:6px solid var(--bronze);} 
    .stAlert.warning{background:#fffbe5; border-left:6px solid var(--taupe);} 
    </style>
    """,
    unsafe_allow_html=True,
)

# ───────────────────────────────────────── Branding
logo = Image.open("umbra_logo_white_rgb.png")
st.image(logo, width=240)

st.title("Blind System – Whole‑Year Energy Impact (London)")

# ───────────────────────────────────────── Climate Data (monthly)
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
GHI =  [24, 43, 75,105,132,140,145,135,100, 64, 35, 23]  # kWh/m²·mo (St James’s Park)
HDD =  [300,255,205,115, 55, 18, 11, 25, 80,165,240,290] # °C·day / mo (base 18 °C)
irradiance = pd.Series(GHI, index=MONTHS)
hdd        = pd.Series(HDD, index=MONTHS)

# ───────────────────────────────────────── Defaults
DEFAULT = dict(
    area=44_800,  # m² glazed (Shard minus hotel floors)
    motor_old=120, motor_new=10, standby=0.5, moves=6, blinds=1000,
    days=260,
    usage_old=0.80, usage_new=1.00,
    shgc=0.12, shade_eff=0.90,
    u_glass=1.2, delta_u=0.15,
    cop=3.0,
    c_ele=0.20, c_heat=0.10,
)

# ───────────────────────────────────────── Sidebar Inputs
with st.sidebar:
    st.header("Model Inputs")
    area = st.number_input("Window Area (m²)", value=DEFAULT['area'],
                           help="Total curtain‑wall area modelled (hotel floors excluded).")

    st.subheader("Blind Usage (share of beneficial hours closed)")
    usage_old = st.slider("Existing system", 0.0, 1.0, DEFAULT['usage_old'], 0.05,
                          help="Fraction of time legacy blinds are deployed when beneficial.")
    usage_new = st.slider("New system", 0.0, 1.0, DEFAULT['usage_new'], 0.05,
                          help="Expected optimal deployment rate of new blinds.")

    st.subheader("Motor & Movements")
    motor_old = st.number_input("Motor Power – OLD (W)", 1, 500, DEFAULT['motor_old'],
                               help="Active draw of one old motor while moving.")
    motor_new = st.number_input("Motor Power – NEW (W)", 1, 500, DEFAULT['motor_new'],
                               help="Active draw of one new motor while moving.")
    standby   = st.number_input("Stand‑by Power (W)", 0.0, 5.0, DEFAULT['standby'], 0.1,
                               help="Idle draw per motor when not moving.")
    moves_day = st.number_input("Movements per blind per day", 0, 20, DEFAULT['moves'],
                               help="Average full‑travel cycles per blind each day.")
    n_blinds  = st.number_input("Quantity of blinds", 1, 10_000, DEFAULT['blinds'],
                               help="Total motorised blinds in scope.")

    st.subheader("Thermal & Economic")
    shgc = st.number_input("Fabric SHGC", 0.05, 0.9, DEFAULT['shgc'], 0.01,
                           help="Solar‑heat‑gain coefficient of blind fabric.")
    shade_eff = st.slider("Shade effectiveness", 0.0, 1.0, DEFAULT['shade_eff'], 0.05,
                          help="Fraction of solar blocked when blind is closed.")
    u_glass = st.number_input("Bare glass U (W/m²K)", 0.5, 3.0, DEFAULT['u_glass'], 0.05,
                             help="Thermal transmittance of glazing alone.")
    delta_u = st.number_input("ΔU with blind closed", 0.0, 0.5, DEFAULT['delta_u'], 0.01,
                             help="U‑value reduction achieved by closed blind.")
    cop = st.number_input("Cooling COP", 1.0, 6.0, DEFAULT['cop'], 0.1,
                          help="Coefficient of performance of cooling plant.")
    c_ele = st.number_input("Electricity £/kWh", 0.05, 0.50, DEFAULT['c_ele'], 0.01,
                           help="Rate for electricity (motors & cooling).")
    c_heat = st.number_input("Heating £/kWh", 0.03, 0.30, DEFAULT['c_heat'], 0.01,
                            help="Heating energy tariff.")

# ───────────────────────────────────────── Helper

def motor_kwh(active_W, standby_W, usage, moves, days, n):
    active_h = moves * 0.01  # assume 1 cycle = 36 s
    kwh = ((active_W*active_h*days*usage) + (standby_W*(24-active_h)*days*(1-usage))) / 1000
    return kwh * n

# ───────────────────────────────────────── Annual Loads
solar_gain_old = shgc * (1 - usage_old*shade_eff) * irradiance * area
solar_gain_new = shgc * (1 - usage_new*shade_eff) * irradiance * area
cool_old = (solar_gain_old / cop).sum()
cool_new = (solar_gain_new / cop).sum()

U_old = u_glass - usage_old*delta_u
U_new = u_glass - usage_new*delta_u
heat_old = (U_old * area * hdd * 24 / 1000).sum()
heat_new = (U_new * area * hdd * 24 / 1000).sum()

motor_old = motor_kwh(motor_old, standby, usage_old, moves_day, DEFAULT['days'], n_blinds)
motor_new = motor_kwh(motor_new, standby, usage_new, moves_day, DEFAULT['days'], n_blinds)

# Costs
cost_motor_old = motor_old * c_ele
cost_motor_new = motor_new * c_ele
cost_cool_old  = cool_old  * c_ele
cost_cool_new  = cool_new  * c_ele
cost_heat_old  = heat_old  * c_heat
cost_heat_new  = heat_new  * c_heat

# ───────────────────────────────────────── Formatting
fmt = lambda x: f"{x:,.2f}"
cur = lambda x: f"£{x:,.2f}"

# ───────────────────────────────────────── Outputs
st.header("📊 Results & Savings")

# Motor Table
st.subheader("Motor Consumption ⚡")
st.table(pd.DataFrame({
    "Existing": [fmt(motor_old), cur(cost_motor_old)],
    "New":      [fmt(motor_new),  cur(cost_motor_new)],
    "Savings":  [fmt(motor_old-motor_new), cur(cost_motor_old-cost_motor_new)]
}, index=["kWh / year","£ / year"]))

# Thermal Table
st.subheader("Thermal Performance 🏢")
st.table(pd.DataFrame({
    "Existing": [fmt(cool_old), cur(cost_cool
