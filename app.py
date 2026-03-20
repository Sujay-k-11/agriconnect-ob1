import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import matplotlib.pyplot as plt

# ═══════════════════════════════════════════════════════
# Load Model & Files
# ═══════════════════════════════════════════════════════
@st.cache_resource
def load_model():
    model = joblib.load("model.pkl")
    with open("model_features.json") as f:
        features = json.load(f)
    with open("lease_rates.json") as f:
        lease_rates = json.load(f)
    return model, features, lease_rates

@st.cache_data
def load_data():
    prices = pd.read_csv("crop_prices.csv")
    yields = pd.read_csv("crop_yield.csv")
    return prices, yields

model, model_features, LEASE_RATES = load_model()
price_df, yield_df = load_data()
DEFAULT_LEASE = {"min": 6000, "avg": 10000, "max": 16000}

# ═══════════════════════════════════════════════════════
# Predict Function
# ═══════════════════════════════════════════════════════
def predict_income(price, yield_kg, month, state, crop):
    sample = pd.DataFrame(columns=model_features)
    sample.loc[0] = 0
    sample["price_modal"]     = price
    sample["avg_yield_kg_ha"] = yield_kg
    sample["month"]           = month
    state_col = "state_" + state
    if state_col in sample.columns:
        sample[state_col] = 1
    crop_col = "crop_" + crop
    if crop_col in sample.columns:
        sample[crop_col] = 1
    return model.predict(sample)[0]

# ═══════════════════════════════════════════════════════
# Get Price & Yield from CSV
# ═══════════════════════════════════════════════════════
def get_price(state, crop):
    row = price_df[
        (price_df["state"].str.lower() == state.lower()) &
        (price_df["crop"].str.lower()  == crop.lower())
    ]
    return row["avg_price_quintal"].values[0] if not row.empty else None

def get_yield(state, crop):
    row = yield_df[
        (yield_df["state"].str.lower() == state.lower()) &
        (yield_df["crop"].str.lower()  == crop.lower())
    ]
    if not row.empty:
        return row["avg_yield_kg_ha"].values[0]
    nat = yield_df[yield_df["crop"].str.lower() == crop.lower()]
    return nat["avg_yield_kg_ha"].mean() if not nat.empty else 25000

# ═══════════════════════════════════════════════════════
# Page Config
# ═══════════════════════════════════════════════════════
st.set_page_config(page_title="AgriConnect+", page_icon="🌾", layout="centered")

st.title("🌾 AgriConnect+")
st.subheader("Crop Income vs Lease Income Comparison")
st.markdown("**Select your state and crop — we'll predict which option gives you more income!**")
st.divider()

# ═══════════════════════════════════════════════════════
# Dropdowns
# ═══════════════════════════════════════════════════════
available_states = sorted(price_df["state"].dropna().unique().tolist())
available_crops  = sorted(price_df["crop"].dropna().unique().tolist())

col1, col2 = st.columns(2)

with col1:
    state = st.selectbox("📍 Select State", available_states)
    month = st.slider("📅 Select Month", min_value=1, max_value=12, value=6)

with col2:
    state_crops = sorted(
        price_df[price_df["state"].str.lower() == state.lower()]["crop"].unique().tolist()
    )
    if not state_crops:
        state_crops = available_crops
    crop  = st.selectbox("🌱 Select Crop", state_crops)
    acres = st.number_input("🏡 Land Size (Acres)", min_value=0.5,
                             max_value=1000.0, value=2.0, step=0.5)

st.divider()

# ═══════════════════════════════════════════════════════
# Auto-fetch Price & Yield
# ═══════════════════════════════════════════════════════
price    = get_price(state, crop)
yield_kg = get_yield(state, crop)

c1, c2 = st.columns(2)
with c1:
    if price:
        st.info(f"📊 **Avg Mandi Price**\n\n₹{price:,.2f} per quintal")
    else:
        st.warning("⚠️ No price data for this combination.")
        price = st.number_input("Enter price manually (Rs/quintal)",
                                min_value=0.0, value=1200.0, step=50.0)
with c2:
    st.info(f"🌾 **Avg Yield**\n\n{yield_kg:,.0f} kg per hectare")

st.divider()

# ═══════════════════════════════════════════════════════
# Lease Rate
# ═══════════════════════════════════════════════════════
lease_data   = LEASE_RATES.get(state, DEFAULT_LEASE)
lease_min    = lease_data["min"]
lease_avg    = lease_data["avg"]
lease_max    = lease_data["max"]

st.markdown("### 🏠 Lease Rate")
st.info(f"📍 **{state}** lease rates per acre/year:\n\n"
        f"Min: ₹{lease_min:,} | Avg: ₹{lease_avg:,} | Max: ₹{lease_max:,}\n\n"
        f"*(Source: NITI Aayog Agricultural Land Leasing Report)*")

lease_choice = st.radio(
    "Select lease rate to compare with:",
    ["Minimum", "Average", "Maximum"],
    index=1, horizontal=True
)
lease_per_acre = {"Minimum": lease_min, "Average": lease_avg, "Maximum": lease_max}[lease_choice]

st.divider()

# ═══════════════════════════════════════════════════════
# Compare Button
# ═══════════════════════════════════════════════════════
if st.button("🔍 Compare Income", use_container_width=True, type="primary"):

    crop_per_acre  = predict_income(price, yield_kg, month,
                                    state.strip().title(),
                                    crop.strip().title())
    total_crop     = crop_per_acre * acres
    total_lease    = lease_per_acre * acres
    difference     = total_crop - total_lease
    margin_pct     = abs(difference / total_lease) * 100 if total_lease > 0 else 0
    better         = "🌾 Crop Farming" if difference > 0 else "🏠 Leasing Land"

    st.markdown("## 📊 Results")

    m1, m2, m3 = st.columns(3)
    m1.metric("🌾 Crop Income",  f"₹{total_crop:,.0f}",  f"₹{crop_per_acre:,.0f}/acre")
    m2.metric("🏠 Lease Income", f"₹{total_lease:,.0f}", f"₹{lease_per_acre:,}/acre")
    m3.metric("💰 Difference",   f"₹{abs(difference):,.0f}", f"{margin_pct:.1f}% advantage")

    st.divider()

    if difference > 0:
        st.success(
            f"✅ **Best Option: {better}**\n\n"
            f"Growing **{crop}** on your {acres}-acre land in **{state}** "
            f"earns ₹{abs(difference):,.0f} MORE than leasing it out.\n\n"
            f"That's **{margin_pct:.1f}% more income** by farming! 🚀"
        )
    else:
        st.warning(
            f"⚠️ **Best Option: {better}**\n\n"
            f"Leasing your {acres}-acre land in **{state}** "
            f"earns ₹{abs(difference):,.0f} MORE than growing **{crop}** right now.\n\n"
            f"Consider a different crop or lease your land this season."
        )

    st.divider()

    # Bar Chart
    fig, ax = plt.subplots(figsize=(7, 4))
    values  = [total_crop, total_lease]
    labels  = ["Crop Farming", "Leasing Land"]
    colors  = ["#2ecc71" if total_crop >= total_lease else "#e74c3c",
               "#2ecc71" if total_lease > total_crop  else "#e74c3c"]

    bars = ax.bar(labels, values, color=colors, width=0.4, edgecolor="white")
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.02,
                f"₹{val:,.0f}", ha="center", fontsize=12, fontweight="bold")

    ax.set_title(f"{crop} Farming vs Leasing — {state} ({acres} acres)",
                 fontsize=13, fontweight="bold", pad=15)
    ax.set_ylabel("Total Income (₹)", fontsize=11)
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
            "Mandi Price", "Yield",
            "Crop Income/Acre", "Total Crop Income",
            "Lease Rate/Acre", "Total Lease Income",
            "Difference", "Better Option"
        ],
        "Value": [
            state, crop, month, f"{acres} acres",
            f"₹{price:,.2f}/quintal", f"{yield_kg:,.0f} kg/ha",
            f"₹{crop_per_acre:,.2f}", f"₹{total_crop:,.2f}",
            f"₹{lease_per_acre:,}", f"₹{total_lease:,.2f}",
            f"₹{abs(difference):,.2f}", better
        ]
    })
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.caption(f"ℹ️ Lease rates for {state}: ₹{lease_min:,}–₹{lease_max:,}/acre/year "
               f"(NITI Aayog). Compared using **{lease_choice.lower()}** rate.")
