import streamlit as st
import pandas as pd

st.title("Valora")

# --- Ladda in data ---
df = pd.read_csv("https://raw.githubusercontent.com/cb2cb/cb-machinelearning/refs/heads/master/fundamental_data.csv")
st.dataframe(df)

# --- Välj bolag ---
ticker = st.selectbox("Välj bolag:", df["Ticker"].unique())
row = df[df["Ticker"] == ticker].iloc[0]

# --- Grundparametrar för modellen ---
discount_rate = 0.08       # 8 % diskonteringsränta
terminal_growth = 0.02     # Terminal tillväxt 2 %
years = 5

def intrinsic_value_dcf(fcf, cagr, discount_rate, years, terminal_growth):
    future_cf = [fcf * ((1 + cagr) ** t) for t in range(1, years + 1)]
    discounted_cf = [cf / ((1 + discount_rate) ** t) for t, cf in enumerate(future_cf, 1)]
    terminal_value = future_cf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    discounted_terminal = terminal_value / ((1 + discount_rate) ** years)
    return sum(discounted_cf) + discounted_terminal

# --- FCF per aktie ---
if row["Price"] > 0 and row["FreeCashflow"] > 0 and row["MarketCap"] > 0:
    shares = row["MarketCap"] / row["Price"]
    fcf_per_share = row["FreeCashflow"] / shares

    # Använd kolumnen "TwoYearCAGR_orelse3%" för tillväxt
    cagr = row.get("TwoYearCAGR_orelse3%", 0.03)

    # Säkerställ rimligt värde för CAGR
    if cagr <= 0 or cagr > 0.3:
        cagr = 0.03

    intrinsic_val = intrinsic_value_dcf(fcf_per_share, cagr, discount_rate, years, terminal_growth)

    st.subheader("📈 Diskonteringsmodell (Intrinsic Value)")
    st.metric("Intrinsic Value (SEK)", f"{intrinsic_val:.2f}")
    diff = (intrinsic_val - row["Price"]) / row["Price"] * 100
    if diff > 0:
        st.success(f"💰 Undervärderad med {diff:.1f} %")
    else:
        st.warning(f"📉 Övervärderad med {abs(diff):.1f} %")
else:
    st.info("Otillräcklig data (FCF, Price eller MarketCap saknas).")
