import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json

# ═══════════════════════════════════════════════════════
# Load Data
# ═══════════════════════════════════════════════════════
@st.cache_data
def load_data():
    prices = pd.read_csv("crop_prices.csv")
    yields = pd.read_csv("crop_yield.csv")
    with open("lease_rates.json") as f:
        lease_rates = json.load(f)
    return prices, yields, lease_rates

price_df, yield_df, LEASE_RATES = load_data()
DEFAULT_LEASE = {"min": 30000, "avg": 50000, "max": 80000}

# ═══════════════════════════════════════════════════════
# Realistic Farming Cost per Acre (Rs)
# ═══════════════════════════════════════════════════════
FARMING_COSTS = {
    'Amaranthus':   8000,
    'Banana':      35000,
    'Beans':       12000,
    'Beetroot':    10000,
    'Bitter Gourd':12000,
    'Bottle Gourd':10000,
    'Brinjal':     12000,
    'Cabbage':     12000,
    'Capsicum':    18000,
    'Carrot':      15000,
    'Cauliflower': 14000,
    'Coconut':     20000,
    'Cotton':      18000,
    'Garlic':      25000,
    'Grapes':      45000,
    'Green Chilli':15000,
    'Groundnut':   18000,
    'Guava':       20000,
    'Lemon':       18000,
    'Maize':       12000,
    'Mango':       20000,
    'Mustard':     10000,
    'Onion':       18000,
    'Orange':      20000,
    'Papaya':      22000,
    'Pomegranate': 35000,
    'Potato':      20000,
    'Pumpkin':     10000,
    'Rice':        22000,
    'Soyabean':    10000,
    'Spinach':      8000,
    'Sugarcane':   25000,
    'Sunflower':   10000,
    'Tomato':      18000,
    'Turmeric':    22000,
    'Wheat':       12000,
}

# ═══════════════════════════════════════════════════════
# Functions
# ═══════════════════════════════════════════════════════
def get_price(state, crop):
    row = price_df[
        (price_df["state"].str.lower() == state.lower()) &
        (price_df["crop"].str.lower()  == crop.lower())
    ]
    return row["avg_price_quintal"].values[0] if not row.empty else None

def get_yield(state, crop, irrigation):
    row = yield_df[
        (yield_df["state"].str.lower() == state.lower()) &
        (yield_df["crop"].str.lower()  == crop.lower())
    ]
    if not row.empty:
        base_yield = row["avg_yield_kg_ha"].values[0]
    else:
        nat = yield_df[yield_df["crop"].str.lower() == crop.lower()]
        base_yield = nat["avg_yield_kg_ha"].mean() if not nat.empty else 4000

    if irrigation == "Rainfed":
        return base_yield * 0.8
    else:
        return base_yield * 1.2

def estimate_cost(crop, acres):
    base_cost = FARMING_COSTS.get(crop, 15000)
    return base_cost * acres

# ═══════════════════════════════════════════════════════
# Page Config
# ═══════════════════════════════════════════════════════
st.set_page_config(page_title="AgriConnect+", page_icon="🌾", layout="centered")

st.title("🌾 AgriConnect+")
st.subheader("Crop Income vs Lease Income Comparison")
st.markdown("**Find whether farming or leasing gives you more profit**")
st.divider()

# ═══════════════════════════════════════════════════════
# Inputs
# ═══════════════════════════════════════════════════════
available_states = sorted(price_df["state"].dropna().unique().tolist())
available_crops  = sorted(price_df["crop"].dropna().unique().tolist())

col1, col2 = st.columns(2)

with col1:
    state      = st.selectbox("📍 State", available_states)
    irrigation = st.selectbox("💧 Irrigation Type", ["Irrigated", "Rainfed"])
    month      = st.slider("📅 Harvest Month", 1, 12, 6)

with col2:
    state_crops = sorted(
        price_df[price_df["state"].str.lower() == state.lower()]["crop"].unique().tolist()
    )
    if not state_crops:
        state_crops = available_crops
    crop  = st.selectbox("🌱 Crop", state_crops)
    acres = st.number_input("🏡 Land Size (Acres)", 0.5, 1000.0, 2.0, step=0.5)

st.divider()

# ═══════════════════════════════════════════════════════
# Price & Yield
# ═══════════════════════════════════════════════════════
price    = get_price(state, crop)
yield_kg = get_yield(state, crop, irrigation)

# Market Scenario
risk = st.radio("📊 Market Scenario",
                ["Low (Bad Season)", "Average", "High (Good Season)"],
                index=1, horizontal=True)

if price:
    if "Low" in risk:
        price *= 0.8
    elif "High" in risk:
        price *= 1.2

c1, c2 = st.columns(2)
with c1:
    if price:
        st.info(f"📊 **Avg Mandi Price**\n\n₹{price:,.0f} / quintal\n\n*({risk} scenario)*")
    else:
        st.warning("⚠️ No price data — enter manually")
        price = st.number_input("Enter price manually (Rs/quintal)",
                                0.0, 100000.0, 2500.0, step=100.0)
with c2:
    st.info(f"🌾 **Avg Yield**\n\n{yield_kg:,.0f} kg/hectare\n\n*({irrigation})*")

st.divider()

# ═══════════════════════════════════════════════════════
# Lease Rate
# ═══════════════════════════════════════════════════════
lease_data = LEASE_RATES.get(state, DEFAULT_LEASE)
lease_min  = lease_data["min"]
lease_avg  = lease_data["avg"]
lease_max  = lease_data["max"]

st.markdown("### 🏠 Lease Rate")
st.info(f"📍 **{state}** lease rates per acre/year:\n\n"
        f"Min: ₹{lease_min:,} | Avg: ₹{lease_avg:,} | Max: ₹{lease_max:,}\n\n"
        f"*(Source: NITI Aayog Agricultural Land Leasing Report)*")

lease_choice = st.radio(
    "Select lease rate:",
    ["Minimum", "Average", "Maximum"],
    index=1, horizontal=True
)
lease_per_acre = {"Minimum": lease_min,
                  "Average": lease_avg,
                  "Maximum": lease_max}[lease_choice]

st.divider()

# ═══════════════════════════════════════════════════════
# Compare Button
# ═══════════════════════════════════════════════════════
if st.button("🔍 Compare Income", use_container_width=True, type="primary"):

    # Yield per acre in quintals
    # 1 hectare = 2.47 acres, 1 quintal = 100 kg
    yield_quintal_acre = (yield_kg / 100) / 2.47

    # Gross income per acre
    gross_per_acre    = yield_quintal_acre * price
    total_gross       = gross_per_acre * acres

    # Farming cost
    total_cost        = estimate_cost(crop, acres)

    # Net crop income
    net_crop_income   = total_gross - total_cost

    # Lease income
    total_lease       = lease_per_acre * acres

    # Comparison
    difference        = net_crop_income - total_lease
    better            = "🌾 Crop Farming" if difference > 0 else "🏠 Leasing Land"
    margin_pct        = abs(difference / total_lease) * 100 if total_lease > 0 else 0

    # ── Results ───────────────────────────────────
    st.markdown("## 📊 Results")

    # Cost info
    st.info(f"💸 **Estimated Farming Cost:** ₹{total_cost:,.0f} "
            f"(₹{FARMING_COSTS.get(crop, 15000):,}/acre × {acres} acres)")

    m1, m2, m3 = st.columns(3)
    m1.metric("🌾 Net Crop Income",  f"₹{net_crop_income:,.0f}",
              f"₹{gross_per_acre:,.0f} gross/acre")
    m2.metric("🏠 Lease Income",     f"₹{total_lease:,.0f}",
              f"₹{lease_per_acre:,}/acre")
    m3.metric("💰 Difference",       f"₹{abs(difference):,.0f}",
              f"{margin_pct:.1f}% advantage")

    st.divider()

    # Recommendation
    if difference > 0:
        st.success(
            f"✅ **Best Option: {better}**\n\n"
            f"Growing **{crop}** on your {acres}-acre land in **{state}** "
            f"gives **₹{abs(difference):,.0f} MORE profit** than leasing!\n\n"
            f"That's **{margin_pct:.1f}% more** after farming costs. 🚀"
        )
    else:
        st.warning(
            f"⚠️ **Best Option: {better}**\n\n"
            f"Leasing your {acres}-acre land in **{state}** gives "
            f"**₹{abs(difference):,.0f} MORE** than growing **{crop}**.\n\n"
            f"Consider a higher-value crop or lease your land this season."
        )

    st.divider()

    # Bar Chart
    fig, ax = plt.subplots(figsize=(7, 4))
    values  = [net_crop_income, total_lease]
    labels  = ["Net Crop Income", "Lease Income"]
    colors  = ["#2ecc71" if net_crop_income >= total_lease else "#e74c3c",
               "#2ecc71" if total_lease > net_crop_income  else "#e74c3c"]

    bars = ax.bar(labels, values, color=colors, width=0.4, edgecolor="white")
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + max(values)*0.02,
                f"₹{val:,.0f}", ha="center", fontsize=11, fontweight="bold")

    ax.set_title(f"{crop} — {state} ({acres} acres, {irrigation}, {risk.split()[0]} market)",
                 fontsize=12, fontweight="bold")
    ax.set_ylabel("Income (₹)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x:,.0f}"))
    plt.tight_layout()
    st.pyplot(fig)

    st.divider()

    # Summary Table
    st.markdown("### 📋 Summary")
    summary = pd.DataFrame({
        "Parameter": [
            "State", "Crop", "Month", "Land Size",
            "Irrigation", "Market Scenario",
            "Mandi Price", "Yield",
            "Gross Crop Income", "Farming Cost",
            "Net Crop Income", "Lease Income",
            "Difference", "Best Option"
        ],
        "Value": [
            state, crop, month, f"{acres} acres",
            irrigation, risk,
            f"₹{price:,.0f}/quintal", f"{yield_kg:,.0f} kg/ha",
            f"₹{total_gross:,.0f}", f"₹{total_cost:,.0f}",
            f"₹{net_crop_income:,.0f}", f"₹{total_lease:,.0f}",
            f"₹{abs(difference):,.0f}", better
        ]
    })
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.caption(
        f"ℹ️ Lease rates for {state}: ₹{lease_min:,}–₹{lease_max:,}/acre/year "
        f"(NITI Aayog). Using **{lease_choice.lower()}** rate of ₹{lease_per_acre:,}/acre."
    )
