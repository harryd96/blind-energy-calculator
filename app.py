https://blind-energy-calculator-okdq6vwxykz2qrztyvwy5w.streamlit.app/

# ───────────────────── Helper Functions ─────────────────────

def motor_kwh(active, standby, usage, moves, days, n):
    active_h = moves * 0.01  # 1 cycle ≈36 s
    return (((active*active_h*days*usage) + (standby*(24-active_h)*days*(1-usage))) / 1000) * n

fmt = lambda x: f"{x:,.2f}"
cur = lambda x: f"£{x:,.2f}"

# ───────────────────── Energy & Cost Calculations ─────────────────────
solar_gain_old = SHGC_OLD * (1 - usage_old*shade_eff) * irradiance * area
solar_gain_new = shgc_new * (1 - usage_new*shade_eff) * irradiance * area
cool_old, cool_new = (solar_gain_old/cop).sum(), (solar_gain_new/cop).sum()

U_old, U_new = u_glass - usage_old*delta_u, u_glass - usage_new*delta_u
heat_old = (U_old*area*hdd*24/1000).sum()
heat_new = (U_new*area*hdd*24/1000).sum()

motor_old_kwh = motor_kwh(motor_old, standby, usage_old, moves_day, DEFAULT["days"], n_blinds)
motor_new_kwh = motor_kwh(motor_new, standby, usage_new, moves_day, DEFAULT["days"], n_blinds)

cost_motor_old, cost_motor_new = motor_old_kwh*c_ele, motor_new_kwh*c_ele
cost_cool_old,  cost_cool_new  = cool_old*c_ele,      cool_new*c_ele
cost_heat_old,  cost_heat_new  = heat_old*c_heat,     heat_new*c_heat

# ───────────────────── Carbon Savings ─────────────────────
co2_elec_saved = (motor_old_kwh - motor_new_kwh + cool_old - cool_new) * ELEC_CO2
co2_heat_saved = (heat_old - heat_new) * HEAT_CO2
co2_total_kg   = co2_elec_saved + co2_heat_saved
co2_total_t    = co2_total_kg / 1000
TREES_EQ       = int(round(co2_total_kg / TREE_CO2))
FLIGHTS_EQ     = int(round(co2_total_t / FLIGHT_CO2))

# ───────────────────── Outputs ─────────────────────
st.header("📊 Results & Savings")

st.subheader("Motor Consumption ⚡")
motor_df = pd.DataFrame({
    "Existing": [fmt(motor_old_kwh), cur(cost_motor_old)],
    "New":      [fmt(motor_new_kwh), cur(cost_motor_new)],
    "Savings":  [fmt(motor_old_kwh - motor_new_kwh), cur(cost_motor_old - cost_motor_new)]
}, index=["kWh / yr", "£ / yr"])

st.table(motor_df)

st.subheader("Thermal Performance 🏢")
thermal_df = pd.DataFrame({
    "Existing": [fmt(cool_old), cur(cost_cool_old), fmt(heat_old), cur(cost_heat_old)],
    "New":      [fmt(cool_new), cur(cost_cool_new), fmt(heat_new), cur(cost_heat_new)],
    "Savings":  [fmt(cool_old - cool_new), cur(cost_cool_old - cost_cool_new), fmt(heat_old - heat_new), cur(cost_heat_old - cost_heat_new)]
}, index=["Cooling kWh / yr", "Cooling £ / yr", "Heating kWh / yr", "Heating £ / yr"])

st.table(thermal_df)

energy_saved = (motor_old_kwh - motor_new_kwh) + (cool_old - cool_new) + (heat_old - heat_new)
cost_saved = (cost_motor_old - cost_motor_new) + (cost_cool_old - cost_cool_new) + (cost_heat_old - cost_heat_new)

st.markdown(f"### 💰 **Total Annual Energy Saved:** {fmt(energy_saved)} kWh")
st.markdown(f"### 💰 **Total Annual Cost Saved:** {cur(cost_saved)}")

if cost_saved > 0:
    st.success("New system delivers annual cost savings under current assumptions.")
else:
    st.warning("New system increases annual cost. Adjust inputs or usage assumptions.")

# ───────────────────── Carbon Messaging ─────────────────────
st.markdown("---")
st.subheader("🌍 Carbon Impact")
st.markdown(f"**Total CO₂ Saved:** ≈ {fmt(co2_total_kg)} kg ({fmt(co2_total_t)} t)")
st.markdown(f"🌳 Equivalent to saving emissions from ~{TREES_EQ} mature trees")
st.markdown(f"✈️ Or avoiding ~{FLIGHTS_EQ} London–NYC round‑trip flights")

st.caption("Monthly GHI & HDD source: London St James’s Park TMY · All £, kWh & CO₂ rounded to two decimals.")

st.caption("\nDisclaimer: This model is a simplified energy estimation tool. It does not account for real-world variables such as occupancy patterns, equipment usage, or seasonal shading strategies. It should not be used to predict actual energy bills or carbon savings with precision. For detailed assessments, a full building energy simulation is recommended.")
