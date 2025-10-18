import streamlit as st
import pandas as pd

st.title("Valora 🇸🇪")

# --- Ladda in data ---
df = pd.read_csv("https://raw.githubusercontent.com/cb2cb/cb-machinelearning/refs/heads/master/fundamental_data.csv")
st.dataframe(df)

# --- Svensk WACC ---
def calc_wacc(market_cap, total_debt=0, cash=0, beta=1.0, tax_rate=0.20):
    risk_free = 0.025       # 10-årig statsobligation
    market_premium = 0.055  # riskpremie
    re = risk_free + beta * market_premium
    rd = risk_free + 0.015  # schablon
    E, D = market_cap, total_debt
    V = E + D if E + D > 0 else 1
    return round((E/V) * re + (D/V) * rd * (1 - tax_rate), 4)

# --- Välj bolag ---
ticker = st.selectbox("Välj bolag:", df["Ticker"].unique())
row = df[df["Ticker"] == ticker].iloc[0]

# --- Uppskatta skulder ---
total_debt = row["MarketCap"] * (row["Debt/Equity"] / 100) if row["Debt/Equity"] > 0 else 0

# --- Beräkna WACC ---
wacc = calc_wacc(row["MarketCap"], total_debt, beta=row["Beta"])

if wacc:
    st.metric("Beräknad WACC", f"{wacc*100:.2f}%")
else:
    st.warning("WACC kunde inte beräknas.")

# --- DCF på per-aktie-nivå ---
if row["FreeCashflow"] > 0 and wacc > 0:
    fcf_total = row["FreeCashflow"]
    price = row["Price"]
    shares = row["MarketCap"] / price if price > 0 else 0
    fcf_per_share = fcf_total / shares if shares > 0 else 0

    # Antaganden
    growth_rate = 0.03
    terminal_growth = 0.02
    years = 5

    # Framtida FCF per aktie
    fcfs = [fcf_per_share * ((1 + growth_rate) ** t) for t in range(1, years + 1)]

    # Diskontera
    discounted_fcfs = [fcf / ((1 + wacc) ** t) for t, fcf in enumerate(fcfs, start=1)]

    # Terminalvärde
    fcf_n = fcfs[-1]
    terminal_value = (fcf_n * (1 + terminal_growth)) / (wacc - terminal_growth)
    discounted_terminal = terminal_value / ((1 + wacc) ** years)

    intrinsic_value = sum(discounted_fcfs) + discounted_terminal

    st.subheader("📈 DCF-värdering (per aktie)")
    st.write(f"Intrinsic Value: **{intrinsic_value:.2f} SEK**")

    diff = (intrinsic_value - price) / price * 100
    if diff > 0:
        st.success(f"💰 Undervärderad med {diff:.1f} %.")
    else:
        st.warning(f"📉 Övervärderad med {abs(diff):.1f} %.")
else:
    st.info("Ingen giltig FreeCashflow-data för DCF.")
