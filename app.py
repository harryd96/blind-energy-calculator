import streamlit as st
import pandas as pd
from PIL import Image

"""
Umbra &  |  Whole‑Year Blind Energy Model for The Shard (London)
Brand colours: Bronze #7B7662  · Taupe #C7BB9B
Data source: St James’s Park TMY (GHI & HDD)
Updated 2025‑07‑01
"""

st.set_page_config(page_title="Shard Blind Energy Model", layout="wide")

# ─────────────────────────── Brand Styling ───────────────────────────
st.markdown(
    """
    <style>
    #MainMenu, header, footer {visibility:hidden;}
    .block-container {padding-top:1rem;padding-bottom:1rem;}
    :root {--bronze:#7b7662;--taupe:#c7bb9b;--umbra-black:#000000;}
    h1,h2,h3 {color:var(--bronze);}        /* headings */
    label, .stSlider>label {color:var(--bronze);}  /* sidebar */
    thead {background-color:var(--taupe)!important;color:var(--umbra-black)!important;font-weight:600;}
    tbody tr:nth-child(even){background:#f5f5f5;}
    .stAlert.success{background:#e8f5e9;border-left:6px solid var(--bronze);} 
    .stAlert.warning{background:#fffbe5;border-left:6px solid var(--taupe);} 
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────── Logo ───────────────────────────
logo = Image.open("umbra_logo_white_rgb.png")
st.image(logo, width=260)

st.title("Blind System – Whole‑Year Energy Impact (London)")

# ─────────────────────────── Climate Data (monthly) ───────────────────────────
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
GHI = [24, 43, 75, 105, 132, 140, 145, 135, 100, 64, 35, 23]  # kWh/m²•mo (St James’s Park)
HDD = [300,255,205,115,55,18,11,25,80,165,240,290]            # °C·day / month (base 18 °C)
irradiance = pd.Series(GHI, index=MONTHS)
hdd        = pd.Series(HDD, index=MONTHS)

# ─────────────────────────── Defaults ───────────────────────────
DEFAULT = dict(
    area       = 44_800,    # m² glazed (Shard minus hotel floors)
    motor_old  = 120, motor_new=10, standby=0.5, moves=6, blinds=1000,
    days=260,
    usage_old  = 0.80, usage_new=1.00,
    shgc=0.12, shade_eff=0.90,
    u_glass=1.2, delta_u=0.15,
    cop=3.0, c_ele=0.20, c_heat=0.10,
)

# ─────────────────────────── Sidebar Inputs ───────────────────────────
with st.sidebar:
    st.header("Model Inputs")
    area = st.number_input("Window Area (m²)", value=DEFAULT['area'],
                           help="Total curtain‑wall area analysed (hotel floors excluded).")

    st.subheader("Blind Usage (fraction of beneficial hours closed)")
    usage_old = st.slider("Existing system", 0.0, 1.0, DEFAULT['usage_old'], 0.05,
                          help="Share of hours legacy blinds are deployed when useful.")
    usage_new = st.slider("New system",      0.0, 1.0, DEFAULT['usage_new'], 0.05,
                          help="Expected deployment rate for new blinds (1 = optimally used).")

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
                               help="Total number of motorised blinds in scope.")

    st.subheader("Thermal & Economic")
    shgc = st.number_input("Fabric SHGC", 0.05, 0.9, DEFAULT['shgc'], 0.01,
                           help="Solar‑heat‑gain coefficient of blind fabric.")
    shade_eff = st.slider("Shade effectiveness", 0.0, 1.0, DEFAULT['shade_eff'], 0.05,
                          help="Fraction of incident solar blocked when blind fully closed.")
    u_glass = st.number_input("Bare glass U (W/m²K)", 0.5, 3.0, DEFAULT['u_glass'], 0.05,
                             help="Thermal transmittance of glazing alone (no blind).")
    delta_u = st.number_input("ΔU with blind closed", 0.0, 0.5, DEFAULT['delta_u'], 0.01,
                             help="U‑value reduction achieved when blind is deployed.")
    cop  = st.number_input("Cooling COP", 1.0, 6.0, DEFAULT['cop'], 0.1,
                          help="Coefficient‑of‑performance of cooling plant.")
    c_ele = st.number_input("Electricity £/kWh", 0.05, 0.5, DEFAULT['c_ele'], 0.01,
                           help="Tariff applied to cooling & motor energy.")
    c_heat= st.number_input("Heating £/kWh", 0.03, 0.3, DEFAULT['c_heat'], 0.01,
                           help="Tariff applied to heating load (gas / DHN).")

# ─────────────────────────── Helper Functions ───────────────────────────

def motor_kwh(active_W, standby_W, usage, moves, days, n):
    """Return annual motor kWh for n blinds."""
    active_h = moves * 0.01  # 1 cycle ≈ 36 s
    kwh = ((active_W*active_h*days*usage) + (standby_W*(24-active_h)*days*(1-usage))) / 1000
    return kwh * n

# ─────────────────────────── Annual Cooling (kWh) ───────────────────────────
solar_gain_old = shgc * (1 - usage_old*shade_eff) * irradiance * area  # kWh/mo admitted
solar_gain_new = shgc * (1 - usage_new*shade_eff) * irradiance * area
cool_load_old  = (solar_gain_old / cop).sum()
cool_load_new  = (solar_gain_new / cop).sum()

# ─────────────────────────── Annual Heating (kWh) ───────────────────────────
U_old = u_glass - usage_old*delta_u
U_new = u_glass - usage_new*delta_u
heat_load_old = (U_old * area * hdd * 24 / 1000).sum()
heat_load_new = (U_new * area * hdd * 24 / 1000).sum()

# ─────────────────────────── Motor kWh & Costs ───────────────────────────
motor_old_kwh = motor_kwh(motor_old, standby, usage_old, moves_day, DEFAULT['days'], n_blinds)
motor_new_kwh = motor_kwh(motor_new, standby, usage_new, moves_day, DEFAULT['days'], n_blinds)

c_motor_old = motor_old_kwh * c_ele
c_motor_new = motor_new_kwh * c_ele
c_cool_old  = cool_load_old  * c_ele
c_cool_new  = cool_load_new  * c_ele
c_heat_old  = heat_load_old  * c_heat
c_heat_new  = heat_load_new  * c_heat

# ─────────────────────────── Formatting helpers ───────────────────────────
num = lambda x: f"{x:,.2f}"
cur = lambda x: f"£{x:,.2f}"

# ─────────────────────────── Output Tables ───────────────────────────
st.markdown("## 📊 Results & Savings")

st.subheader("Motor Consumption ⚡")
<|diff_marker|>assistant to=canmore.update_textdoc to=canmore
