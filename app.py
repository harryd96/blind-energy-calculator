# app.py – Umbra Blind Energy Model (carbon-aware, TU/e-informed, sense-checked)
# -----------------------------------------------------------------------------
# Whole-Year Energy, Cost & CO₂ impact for The Shard (London)
# -----------------------------------------------------------------------------

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
    st.image(Image.open("umbra_logo_white_rgb.png"), width=220)
except Exception:
    pass

st.header("Shading at the Shard – Whole-Year Energy Impact")

# ───────────────────── Climate Data (simplified) ─────────────────────
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
GHI = [24,43,75,105,132,140,145,135,100,64,35,23]   # kWh/m²·mo (global horizontal, TMY)
HDD = [300,255,205,115,55,18,11,25,80,165,240,290]  # °C·d / mo (base 18 °C, TMY)
irradiance = pd.Series(GHI, index=MONTHS)
hdd = pd.Series(HDD, index=MONTHS)

# ───────────────────── Defaults & Constants ─────────────────────
DEFAULT = dict(
    area=44_800,
    motor_old=120, motor_new=10, standby=0.5, moves=6,
    blinds=1000, days=260,               # days = operating (lighting + active motor)
    usage_old=0.80, usage_new=1.00,
    u_glass=1.2,
    delta_u_old=0.15, delta_u_new=0.15,
    cop=3.0,
    c_ele=0.20, c_heat=0.10,
    shgc_bare=0.62,                      # typical double glazing SHGC (user-adjustable below)
    aperture=1.00,                       # solar aperture factor (orientation/obstructions)
    lpd=8.0, hours_day=10.0,
)

SHGC_OLD = 0.45  # Existing “with blind down” SHGC (Hexel Screen Vision 5 %)
NEW_FABRICS = {
    "Umbra Alu-Back Screen – SHGC 0.27": 0.27,
    "Umbra White-Back Screen – SHGC 0.34": 0.34,
    "Umbra Standard Screen – SHGC 0.45": 0.45,
}
# ΔU reductions when blind is fully closed (applied as a linear blend by usage)
DELTA_U_FABRIC = {
    "Umbra Alu-Back Screen – SHGC 0.27": 0.20,
    "Umbra White-Back Screen – SHGC 0.34": 0.15,
    "Umbra Standard Screen – SHGC 0.45": 0.10,
}
# Fabrics considered “reflective” for TU/e Kindow effects
REFLECTIVE_FABRICS = {
    "Umbra Alu-Back Screen – SHGC 0.27",
    "Umbra White-Back Screen – SHGC 0.34",
}

ELEC_CO2 = 0.233  # kg CO₂/kWh (electricity)
HEAT_CO2 = 0.184  # kg CO₂/kWh (heating energy)
TREE_CO2 = 22     # kg CO₂ / tree·yr
FLIGHT_CO2 = 1.6  # t CO₂ / London-NYC rtn flight
CALENDAR_DAYS = 365  # standby present all year

# ───────────────────── Sidebar ─────────────────────
with st.sidebar:
    st.header("Model Inputs")

    area = st.number_input(
        "Window Area (m²)",
        value=DEFAULT["area"], min_value=1, step=500,
        help="Total glazed area exposed to sun/daylight. Scales all solar and heat transfer terms linearly."
    )

    st.subheader("Blind Usage (share of beneficial daylight hours closed)")
    usage_old = st.slider(
        "Existing system", 0.0, 1.0, DEFAULT["usage_old"], 0.05,
        help="Fraction of daylight hours the existing blinds are closed when it helps (e.g., glare or cooling). Influences solar gains (cooling) and U-value blending (heating)."
    )
    usage_new = st.slider(
        "New system", 0.0, 1.0, DEFAULT["usage_new"], 0.05,
        help="Fraction of beneficial daylight hours the NEW blinds are closed. Higher values increase insulation benefit (heating ↓) and reduce solar gains (cooling ↓)."
    )

    st.subheader("Motors & Movements")
    motor_old = st.number_input(
        "Motor Power – OLD (W)", 1, 500, DEFAULT["motor_old"],
        help="Active power during movement for the existing motor. Used with movement time to compute active motor kWh."
    )
    motor_new = st.number_input(
        "Motor Power – NEW (W)", 1, 500, DEFAULT["motor_new"],
        help="Active power during movement for the new motor. Lower values mean lower motor energy."
    )
    standby = st.number_input(
        "Stand-by Power (W)", 0.0, 5.0, DEFAULT["standby"], 0.1,
        help="Idle draw per motor when not moving. Applied for 365 days (not just operating days)."
    )
    moves_day = st.number_input(
        "Movements per blind per day", 0, 40, DEFAULT["moves"],
        help="Open/close cycles each day. Movement time is approximated as 0.01 h (36 s) per cycle and scales with usage."
    )
    n_blinds = st.number_input(
        "Quantity of blinds", 1, 20_000, DEFAULT["blinds"],
        help="Total motorised blinds connected. Motor energy scales linearly with this quantity."
    )

    st.subheader("Fabric & SHGC")
    st.markdown(f"**Existing blinds:** Hexel Screen Vision 5 % (SHGC {SHGC_OLD})")
    fabric_key = st.selectbox(
        "New blind fabric (SHGC when down)", list(NEW_FABRICS.keys()),
        help="Select the NEW fabric. The SHGC shown is the effective SHGC when the blind is DOWN. Calculations blend between bare-glass and blind-down SHGC using the usage slider."
    )
    shgc_new = NEW_FABRICS[fabric_key]

    shgc_bare = st.number_input(
        "Bare-glass SHGC (no blind)",
        min_value=0.20, max_value=0.90, value=DEFAULT["shgc_bare"], step=0.01,
        help="Solar Heat Gain Coefficient of the glazing alone. Typical: single ~0.8, double ~0.6. Used to blend to an effective SHGC based on usage."
    )

    aperture = st.number_input(
        "Solar aperture factor",
        min_value=0.10, max_value=1.20, value=DEFAULT["aperture"], step=0.05,
        help="Scales solar irradiance for orientation/shading/tilt (1.0 = as-given GHI on all area). <1 reduces solar; >1 only for rare edge cases."
    )

    st.subheader("Thermal & Economic")
    u_glass = st.number_input(
        "Bare-glass U (W/m²K)", 0.2, 6.0, DEFAULT["u_glass"], 0.05,
        help="Thermal transmittance of glass alone. Lower is better. Used to compute heating load; blinds reduce U when closed."
    )
    delta_u_old = st.number_input(
        "ΔU when existing blind is down (W/m²K)",
        0.0, 1.0, DEFAULT["delta_u_old"], 0.01,
        help="U-value reduction contributed by existing blind when fully down. Effective U is blended by usage."
    )
    delta_u_new = DELTA_U_FABRIC.get(fabric_key, DEFAULT["delta_u_new"])
    st.markdown(
        f"**ΔU when new blind is down:** {delta_u_new:.2f} W/m²K (auto from fabric)"
    )

    cop = st.number_input(
        "Cooling COP", 1.0, 10.0, DEFAULT["cop"], 0.1,
        help="Coefficient Of Performance for cooling: cooling kWh_out per kWh_in. Electrical cooling kWh = (solar heat kWh) / COP."
    )
    c_ele = st.number_input(
        "Electricity £/kWh", 0.00, 5.00, DEFAULT["c_ele"], 0.01,
        help="Tariff for electricity. Applied to motors, lighting and cooling electricity."
    )
    c_heat = st.number_input(
        "Heating £/kWh", 0.00, 5.00, DEFAULT["c_heat"], 0.01,
        help="Tariff for delivered heating energy (e.g., gas/district heat)."
    )

    st.subheader("Control Strategy (TU/e study)")
    strategy = st.selectbox(
        "New system control",
        ["Baseline (irradiance threshold)", "Kindow sun-tracking"],
        help=("Baseline: simple threshold control. "
              "Kindow: sun-tracking logic to keep sun out while preserving view/daylight. "
              "TU/e findings: Kindow+reflective → lighting ↓ ~40%, cooling ↑ ~25%, heating ↓ ~25% vs baseline reflective.")
    )

    st.subheader("Occupancy & Lighting")
    days = st.number_input(
        "Operating days / year", 200, 365, DEFAULT["days"],
        help="Days per year with typical occupancy. Used for lighting and active motor energy."
    )
    hours_day = st.number_input(
        "Occupied hours / day", 1.0, 24.0, DEFAULT["hours_day"], 0.5,
        help="Average daily hours with typical lighting needs."
    )
    lpd = st.number_input(
        "Lighting power density (W/m²)", 0.0, 40.0, DEFAULT["lpd"], 0.5,
        help="Connected lighting load per floor area. Lighting energy = LPD × area × occupied hours."
    )

# ───────────────────── Helper Functions ─────────────────────
def motor_kwh(active_w: float, standby_w: float, usage: float, moves: float,
              operating_days: int, n: int) -> float:
    """
    Annual motor energy (kWh):
      • Active: movements scale with usage (fewer moves if blinds seldom used)
      • Standby: present for 365 days regardless of usage
    """
    active_h_per_day = (moves * max(0.0, min(1.0, usage))) * 0.01  # 1 cycle ≈ 36 s
    standby_h_per_day = max(0.0, 24 - active_h_per_day)
    kwh = (
        active_w * active_h_per_day * operating_days
        + standby_w * standby_h_per_day * CALENDAR_DAYS
    ) / 1000.0
    return kwh * n

fmt = lambda x: f"{x:,.2f}"
cur = lambda x: f"£{x:,.2f}"

# ───────────────────── Lighting (TU/e effects) ─────────────────────
# Baseline lighting demand without daylight control effects
lit_base_kwh = lpd * area * (hours_day * days) / 1000.0  # kWh/yr

def lighting_adjustment(is_reflective: bool, is_kindow: bool) -> float:
    """
    Fractional multiplier for lighting energy:
      • Reflective vs non-reflective under baseline control: ~0.94×
      • Kindow (with reflective fabric): ~0.60× vs baseline reflective
      • If Kindow selected without reflective fabric, fall back to modest benefit (0.85×) or warn.
    """
    if is_kindow and is_reflective:
        return 0.60
    if is_kindow and not is_reflective:
        return 0.85  # conservative fallback if user insists on Kindow + non-reflective
    return 0.94 if is_reflective else 1.00

is_new_reflective = fabric_key in REFLECTIVE_FABRICS
is_kindow = strategy.startswith("Kindow")

# ───────────────────── Solar & Thermal (with SHGC blending) ─────────────────────
# Effective SHGC blends between bare-glass SHGC and blind-down SHGC by usage.
SHGC_eff_old = (1 - usage_old) * shgc_bare + usage_old * SHGC_OLD
SHGC_eff_new = (1 - usage_new) * shgc_bare + usage_new * shgc_new

# Solar gains to the space (kWh heat): SHGC × Irradiance × Area × Aperture
solar_gain_old = SHGC_eff_old * (irradiance * area * aperture)
solar_gain_new = SHGC_eff_new * (irradiance * area * aperture)

# Cooling electricity (kWh): divide heat by COP
cop = max(1.0, cop)  # guard
cool_old = (solar_gain_old / cop).sum()
cool_new = (solar_gain_new / cop).sum()

# Transmission heating (kWh): sum[ U_eff * A * HDD * 24 / 1000 ]
U_floor = 0.20  # floor to avoid non-physical U
U_old = max(U_floor, u_glass - usage_old * delta_u_old)
U_new = max(U_floor, u_glass - usage_new * delta_u_new)
heat_old = (U_old * area * hdd * 24 / 1000.0).sum()
heat_new = (U_new * area * hdd * 24 / 1000.0).sum()

# ───────────────────── Apply TU/e control multipliers to NEW thermal ─────────────────────
# Only when Kindow + reflective fabric (as per study context)
if is_kindow and not is_new_reflective:
    st.warning(
        "Kindow sun-tracking effects are validated for reflective interior fabrics. "
        "Select a reflective fabric (Alu-Back or White-Back) to apply Kindow thermal multipliers. "
        "Lighting uses a conservative benefit in the meantime."
    )

if is_kindow and is_new_reflective:
    cool_new *= 1.25   # more daylight/view time → slightly higher cooling
    heat_new *= 0.75   # more open time but reflective when closed → lower heating

# ───────────────────── Motors ─────────────────────
motor_old_kwh = motor_kwh(motor_old, standby, usage_old, moves_day, days, n_blinds)
motor_new_kwh = motor_kwh(motor_new, standby, usage_new, moves_day, days, n_blinds)

# ───────────────────── Lighting kWh & £ ─────────────────────
lighting_old_kwh = lit_base_kwh * 1.00  # existing assumed non-reflective baseline control
lighting_new_kwh = lit_base_kwh * lighting_adjustment(is_new_reflective, is_kindow)

# ───────────────────── Costs ─────────────────────
cost_motor_old = motor_old_kwh * c_ele
cost_motor_new = motor_new_kwh * c_ele
cost_cool_old  = cool_old      * c_ele
cost_cool_new  = cool_new      * c_ele
cost_heat_old  = heat_old      * c_heat
cost_heat_new  = heat_new      * c_heat
cost_light_old = lighting_old_kwh * c_ele
cost_light_new = lighting_new_kwh * c_ele

# ───────────────────── Carbon ─────────────────────
co2_elec_saved = (
    (motor_old_kwh + cool_old + lighting_old_kwh)
    - (motor_new_kwh + cool_new + lighting_new_kwh)
) * ELEC_CO2
co2_heat_saved = (heat_old - heat_new) * HEAT_CO2
co2_total_kg = co2_elec_saved + co2_heat_saved
co2_total_t = co2_total_kg / 1000.0
TREES_EQ = int(round(co2_total_kg / TREE_CO2)) if co2_total_kg >= 0 else 0
FLIGHTS_EQ = int(round(co2_total_t / FLIGHT_CO2)) if co2_total_t >= 0 else 0

# ───────────────────── Outputs ─────────────────────
st.header("Results & Savings")

# Motors
st.subheader("Motor Consumption")
motor_df = pd.DataFrame({
    "Existing": [fmt(motor_old_kwh), cur(cost_motor_old)],
    "New":      [fmt(motor_new_kwh), cur(cost_motor_new)],
    "Savings":  [fmt(motor_old_kwh - motor_new_kwh), cur(cost_motor_old - cost_motor_new)]
}, index=["kWh / yr", "£ / yr"])
st.table(motor_df)

# Thermal
st.subheader("Thermal Performance")
thermal_df = pd.DataFrame({
    "Existing": [fmt(cool_old), cur(cost_cool_old), fmt(heat_old), cur(cost_heat_old)],
    "New":      [fmt(cool_new), cur(cost_cool_new), fmt(heat_new), cur(cost_heat_new)],
    "Savings":  [fmt(cool_old - cool_new), cur(cost_cool_old - cost_cool_new),
                 fmt(heat_old - heat_new), cur(cost_heat_old - cost_heat_new)]
}, index=["Cooling kWh / yr", "Cooling £ / yr", "Heating kWh / yr", "Heating £ / yr"])
st.table(thermal_df)

# Lighting
st.subheader("Lighting")
light_df = pd.DataFrame({
    "Existing": [fmt(lighting_old_kwh), cur(cost_light_old)],
    "New":      [fmt(lighting_new_kwh), cur(cost_light_new)],
    "Savings":  [fmt(lighting_old_kwh - lighting_new_kwh), cur(cost_light_old - cost_light_new)]
}, index=["kWh / yr", "£ / yr"])
st.table(light_df)

# Totals (site energy)
energy_saved = (
    (motor_old_kwh - motor_new_kwh) +
    (cool_old  - cool_new) +
    (heat_old  - heat_new) +
    (lighting_old_kwh - lighting_new_kwh)
)
cost_saved = (
    (cost_motor_old - cost_motor_new) +
    (cost_cool_old  - cost_cool_new) +
    (cost_heat_old  - cost_heat_new) +
    (cost_light_old - cost_light_new)
)

st.markdown(f"**Total Annual Site Energy Saved:** {fmt(energy_saved)} kWh")
st.markdown(f"**Total Annual Cost Saved:** {cur(cost_saved)}")

# Optional split for clarity
elec_old = motor_old_kwh + cool_old + lighting_old_kwh
elec_new = motor_new_kwh + cool_new + lighting_new_kwh
therm_old = heat_old
therm_new = heat_new
totals_split = pd.DataFrame({
    "Existing": [fmt(elec_old), fmt(therm_old)],
    "New":      [fmt(elec_new), fmt(therm_new)],
    "Savings":  [fmt(elec_old - elec_new), fmt(therm_old - therm_new)],
}, index=["Electricity kWh / yr", "Heating (thermal) kWh / yr"])
st.table(totals_split)

if cost_saved > 0:
    st.success("New system delivers annual cost savings under current assumptions.")
else:
    st.warning("New system increases annual cost. Adjust inputs or usage assumptions.")

# Carbon
st.markdown("---")
st.subheader("Carbon Impact")
st.markdown(f"**Total CO₂ Saved:** ≈ {fmt(co2_total_kg)} kg ({fmt(co2_total_t)} t)")
st.markdown(f"Equivalent to ~{TREES_EQ} mature trees’ annual sequestration")
st.markdown(f"Or avoiding ~{FLIGHTS_EQ} London–NYC round-trip flights")

# Footnotes / assumptions
st.caption(
    "Solar gains use SHGC blending between bare-glass and blind-down SHGC by usage, "
    "applied to monthly GHI and scaled by a solar aperture factor (orientation/obstructions). "
    "Heating uses a blended effective U-value by usage. Motors include standby for 365 days. "
    "Lighting uses LPD × occupied hours with TU/e-informed multipliers for reflective fabrics and Kindow control."
)
st.caption(
    "Monthly GHI & HDD source: London St James’s Park TMY. Site energy totals combine electric and thermal kWh. "
    "This is a simplified estimation tool, not a substitute for whole-building simulation."
)
