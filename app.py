# app.py – Umbra Blind Energy Model (carbon‑aware release)
# -----------------------------------------------------------
# Whole‑Year Energy, Cost & CO₂ impact for The Shard (London)
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

# ───────────────────── Logo & Title ─────────────────────
try:
    st.image(
        Image.open("umbra_logo_white_rgb.png"),
        width=220,
        caption="Umbra Logo"
    )
except Exception:
    st.write("UMBRA &")

st.title("Blind System – Whole‑Year Energy Impact (London)")

# ───────────────────── Climate Data ─────────────────────
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
GHI = [24,43,75,105,132,140,145,135,100,64,35,23]   # kWh/m²·mo
HDD = [300,255,205,115,55,18,11,25,80,165,240,290]  # °C·d / mo (base 18 °C)
irradiance = pd.Series(GHI, index=MONTHS)
hdd = pd.Series(HDD, index=MONTHS)

# ───────────────────── Defaults & Constants ─────────────────────
DEFAULT = dict(
    area=44_800,
    motor_old=120, motor_new=10, standby=0.5, moves=6,
    blinds=1000, days=260,
    usage_old=0.80, usage_new=1.00,
    shade_eff=0.90, u_glass=1.2,
    # Separate ΔU defaults for existing and new systems
    delta_u_old=0.15, delta_u_new=0.15,
    cop=3.0,
    c_ele=0.20, c_heat=0.10,
)

SHGC_OLD = 0.45  # Hexel Screen Vision 5 %
NEW_FABRICS = {
    "Umbra Alu‑Back Screen – SHGC 0.27": 0.27,
    "Umbra White‑Back Screen – SHGC 0.34": 0.34,
    "Umbra Standard Screen – SHGC 0.45": 0.45,
}
# Optional: mapping of fabric to its ΔU impact (reduction in U-value) based on fabric construction
DELTA_U_FABRIC = {
    "Umbra Alu‑Back Screen – SHGC 0.27": 0.20,  # e.g. heavier backed fabric
    "Umbra White‑Back Screen – SHGC 0.34": 0.15,
    "Umbra Standard Screen – SHGC 0.45": 0.10,
}

ELEC_CO2 = 0.233  # kg CO₂/kWh
HEAT_CO2 = 0.184  # kg CO₂/kWh
TREE_CO2 = 22      # kg CO₂ / tree·yr
FLIGHT_CO2 = 1.6   # t CO₂ / London‑NYC rtn flight

# ───────────────────── Sidebar ─────────────────────
with st.sidebar:
    st.header("Model Inputs")

    area = st.number_input(
        "Window Area (m²)",
        value=DEFAULT["area"],
        step=500,
        help="Total glazed window area (m²) used to calculate solar and heat gains."
    )

    st.subheader("Blind Usage (fraction of beneficial hours closed)")
    usage_old = st.slider(
        "Existing system", 0.0, 1.0, DEFAULT["usage_old"], 0.05,
        help="Fraction of daylight hours the existing blinds are closed when solar shading is beneficial (e.g. 0.8 means 80% of sunny periods)."
    )
    usage_new = st.slider(
        "New system", 0.0, 1.0, DEFAULT["usage_new"], 0.05,
        help="Fraction of daylight hours the new automated blinds are closed when shading yields energy savings."
    )

    st.subheader("Motor & Movements")
    motor_old = st.number_input(
        "Motor Power – OLD (W)", 1, 500, DEFAULT["motor_old"],
        help="Power draw of the existing blind motor in Watts during operation. Typical range: 50–150 W."
    )
    motor_new = st.number_input(
        "Motor Power – NEW (W)", 1, 500, DEFAULT["motor_new"],
        help="Power draw of the new blind motor in Watts. Lower values indicate more efficient motors (e.g. 10–50 W)."
    )
    standby = st.number_input(
        "Stand‑by Power (W)", 0.0, 5.0, DEFAULT["standby"], 0.1,
        help="Idle power consumption of the motor when not moving (e.g. 0.1–1 W)."
    )
    moves_day = st.number_input(
        "Movements per blind per day", 0, 20, DEFAULT["moves"],
        help="Number of open/close cycles each blind performs daily (e.g. business hours operation might be 6–10 cycles)."
    )
    n_blinds = st.number_input(
        "Quantity of blinds", 1, 10_000, DEFAULT["blinds"],
        help="Total number of automated blinds in the building or installation."
    )

    st.subheader("Fabric Selection")
    st.markdown(
        f"**Existing blinds:** Hexel Screen Vision 5 % (SHGC {SHGC_OLD})"
    )
    fabric_key = st.selectbox(
        "New blind fabric", list(NEW_FABRICS.keys()),
        help="Select the new fabric option by Solar Heat Gain Coefficient (SHGC). Lower SHGC means less solar heat transmitted."
    )
    shgc_new = NEW_FABRICS[fabric_key]

    st.subheader("Thermal & Economic")
    shade_eff = st.slider(
        "Shade effectiveness", 0.0, 1.0, DEFAULT["shade_eff"], 0.05,
        help="Proportion of solar irradiance blocked by the blind when closed (e.g. 0.9 means 90% blocking)."
    )
    u_glass = st.number_input(
        "Bare glass U (W/m²K)", 0.5, 3.0, DEFAULT["u_glass"], 0.05,
        help=(
            "Thermal transmittance of the bare glazing measured in W/m²K. "
            "Lower U-values indicate better insulation (e.g. single glazing ~5.8, "
            "double glazing ~1.2)."
        )
    )
    # Separate ΔU for existing and auto-derived for new based on fabric
    delta_u_old = st.number_input(
        "ΔU with existing blind closed (W/m²K)",
        0.0, 0.5, DEFAULT["delta_u_old"], 0.01,
        help=(
            "Reduction in U-value when the existing blind is fully closed. "
            "For example, U_glass 1.2 reduced to 1.05 gives ΔU=0.15."
        )
    )
    # automatic ΔU for new fabric, derived from selection
    delta_u_new = DELTA_U_FABRIC.get(fabric_key, DEFAULT["delta_u_new"])
    st.markdown(
        f"**ΔU with new blind closed:** {delta_u_new:.2f} W/m²K (auto-derived based on fabric selection)"
    )
    cop = st.number_input(
        "Cooling COP", 1.0, 6.0, DEFAULT["cop"], 0.1,
        help=(
            "Coefficient Of Performance of the cooling system: ratio of cooling output (kWh) "
            "to electrical input (kWh). Typical COPs range 2–6; e.g. COP=3 means 1 kWh "
            "electricity delivers 3 kWh cooling."
        )
    )
    c_ele = st.number_input(
        "Electricity £/kWh", 0.05, 0.50, DEFAULT["c_ele"], 0.01,
        help="Tariff rate for electricity in £ per kWh. Use local utility rate."
    )
    c_heat = st.number_input(
        "Heating £/kWh", 0.03, 0.30, DEFAULT["c_heat"], 0.01,
        help="Tariff rate for heating energy in £ per kWh (e.g. gas or district heating)."
    )

# ───────────────────── Helper Functions ───────────────────── ───────────────────── ─────────────────────

def motor_kwh(active, standby, usage, moves, days, n):
    """
    Calculate annual motor energy consumption:
    - active draw during movements
    - standby draw when idle
    """
    active_h = moves * 0.01  # 1 cycle ≈36 s
    return (((active * active_h * days * usage)
             + (standby * (24 - active_h) * days * (1 - usage)))
            / 1000) * n

fmt = lambda x: f"{x:,.2f}"
cur = lambda x: f"£{x:,.2f}"

# ───────────────────── Energy & Cost Calculations ─────────────────────
solar_gain_old = SHGC_OLD * (1 - usage_old * shade_eff) * irradiance * area
solar_gain_new = shgc_new * (1 - usage_new * shade_eff) * irradiance * area
cool_old, cool_new = (solar_gain_old / cop).sum(), (solar_gain_new / cop).sum()

U_old = u_glass - usage_old * delta_u_old
U_new = u_glass - usage_new * delta_u_new
heat_old = (U_old * area * hdd * 24 / 1000).sum()
heat_new = (U_new * area * hdd * 24 / 1000).sum()

motor_old_kwh = motor_kwh(
    motor_old, standby, usage_old, moves_day, DEFAULT["days"], n_blinds
)
motor_new_kwh = motor_kwh(
    motor_new, standby, usage_new, moves_day, DEFAULT["days"], n_blinds
)

cost_motor_old = motor_old_kwh * c_ele
cost_motor_new = motor_new_kwh * c_ele
cost_cool_old = cool_old * c_ele
cost_cool_new = cool_new * c_ele
cost_heat_old = heat_old * c_heat
cost_heat_new = heat_new * c_heat

# ───────────────────── Carbon Savings ─────────────────────
co2_elec_saved = (
    motor_old_kwh - motor_new_kwh + cool_old - cool_new
) * ELEC_CO2
co2_heat_saved = (heat_old - heat_new) * HEAT_CO2
co2_total_kg = co2_elec_saved + co2_heat_saved
co2_total_t = co2_total_kg / 1000
TREES_EQ = int(round(co2_total_kg / TREE_CO2))
FLIGHTS_EQ = int(round(co2_total_t / FLIGHT_CO2))

# ───────────────────── Outputs ─────────────────────
st.header("Results & Savings")

st.subheader("Motor Consumption")
motor_df = pd.DataFrame({
    "Existing": [fmt(motor_old_kwh), cur(cost_motor_old)],
    "New": [fmt(motor_new_kwh), cur(cost_motor_new)],
    "Savings": [
        fmt(motor_old_kwh - motor_new_kwh),
        cur(cost_motor_old - cost_motor_new)
    ]
}, index=["kWh / yr", "£ / yr"])

st.table(motor_df)

st.subheader("Thermal Performance")
thermal_df = pd.DataFrame({
    "Existing": [
        fmt(cool_old), cur(cost_cool_old), fmt(heat_old), cur(cost_heat_old)
    ],
    "New": [
        fmt(cool_new), cur(cost_cool_new), fmt(heat_new), cur(cost_heat_new)
    ],
    "Savings": [
        fmt(cool_old - cool_new),
        cur(cost_cool_old - cost_cool_new),
        fmt(heat_old - heat_new),
        cur(cost_heat_old - cost_heat_new)
    ]
}, index=[
    "Cooling kWh / yr", "Cooling £ / yr",
    "Heating kWh / yr", "Heating £ / yr"
])

st.table(thermal_df)

energy_saved = (
    (motor_old_kwh - motor_new_kwh)
    + (cool_old - cool_new)
    + (heat_old - heat_new)
)
cost_saved = (
    (cost_motor_old - cost_motor_new)
    + (cost_cool_old - cost_cool_new)
    + (cost_heat_old - cost_heat_new)
)

st.markdown(f"**Total Annual Energy Saved:** {fmt(energy_saved)} kWh")
st.markdown(f"**Total Annual Cost Saved:** {cur(cost_saved)}")

if cost_saved > 0:
    st.success(
        "New system delivers annual cost savings under current assumptions."
    )
else:
    st.warning(
        "New system increases annual cost. Adjust inputs or usage assumptions."
    )

# ───────────────────── Carbon Messaging ─────────────────────
st.markdown("---")
st.subheader("Carbon Impact")
st.markdown(
    f"**Total CO₂ Saved:** ≈ {fmt(co2_total_kg)} kg ({fmt(co2_total_t)} t)"
)
st.markdown(
    f"Equivalent to saving emissions from ~{TREES_EQ} mature trees"
)
st.markdown(
    f"Or avoiding ~{FLIGHTS_EQ} London–NYC round‑trip flights"
)

st.caption(
    "Monthly GHI & HDD source: London St James’s Park TMY · All £, kWh & CO₂ rounded to two decimals."
)

st.caption(
    "Disclaimer: This model is a simplified energy estimation tool. "
    "It does not account for real-world variables such as occupancy patterns, "
    "equipment usage, or seasonal shading strategies. It should not be used to "
    "predict actual energy bills or carbon savings with precision. For detailed assessments, "
    "a full building energy simulation is recommended."
)
