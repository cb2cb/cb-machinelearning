import streamlit as st
import pandas as pd

st.title("Valora 🇸🇪")

# --- Ladda in data ---
df = pd.read_csv("https://raw.githubusercontent.com/cb2cb/cb-machinelearning/refs/heads/master/fundamental_data.csv")
st.dataframe(df)

# --- Svensk WACC-funktion ---
def calc_wacc(market_cap, total_debt=0, cash=0, beta=1.0, tax_rate=0.20):
    """
    Beräknar WACC (Weighted Average Cost of Capital) för svenska bolag.
    """

    # Svenska standardvärden
    risk_free = 0.025         # 10-årig statsobligation ≈ 2.5 %
    market_premium = 0.055    # svensk riskpremie ≈ 5.5 %
    re = risk_free + beta * market_premium

    # Kostnad för skulder (schablon)
    rd = risk_free + 0.015

    # Kapitalstruktur
    E = market_cap
    D = total_debt
    V = E + D

    if V == 0:
        return None

    wacc = (E/V) * re + (D/V) * rd * (1 - tax_rate)
    return round(wacc, 4)

# --- Välj bolag ---
ticker = st.selectbox("Välj bolag (ticker):", df["Ticker"].unique())
row = df[df["Ticker"] == ticker].iloc[0]

# --- Uppskatta skulder baserat på Debt/Equity ---
if row["Debt/Equity"] > 0:
    total_debt = row["MarketCap"] * (row["Debt/Equity"] / 100)
else:
    total_debt = 0

# --- Beräkna WACC ---
wacc = calc_wacc(
    market_cap=row["MarketCap"],
    total_debt=total_debt,
    beta=row["Beta"]
)

if wacc:
    st.metric("Beräknad WACC", f"{wacc*100:.2f}%")

    if wacc < 0.07:
        st.success("🟢 Låg kapitalkostnad – stabilt, moget bolag.")
    elif wacc < 0.10:
        st.info("🟡 Medelhög kapitalkostnad – balanserad risk.")
    else:
        st.warning("🔴 Hög kapitalkostnad – tillväxt eller hög risk.")
else:
    st.warning("WACC kunde inte beräknas (saknas data).")

# --- Enkel DCF-beräkning baserad på FreeCashflow ---
if row["FreeCashflow"] > 0 and wacc and wacc > 0:
    fcf_now = row["FreeCashflow"]

    # Antaganden
    growth_rate = 0.03       # framtida FCF-tillväxt
    terminal_growth = 0.02   # evig tillväxt
    years = 5                # prognosperiod (år)

    # Prognostisera och diskontera kassaflöden
    fcfs = [fcf_now * ((1 + growth_rate) ** i) for i in range(1, years + 1)]
    discounted_fcfs = [fcf / ((1 + wacc) ** i) for i, fcf in enumerate(fcfs, start=1)]

    # Terminalvärde
    terminal_value = fcfs[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
    discounted_tv = terminal_value / ((1 + wacc) ** years)

    enterprise_value = sum(discounted_fcfs) + discounted_tv

    # Intrinsic Value per aktie (jämför med MarketCap och Price)
    intrinsic_value_per_share = enterprise_value / row["MarketCap"] * row["Price"]

    st.subheader("📈 Enkel DCF-värdering")
    st.write(f"Intrinsic Value (per aktie): **{intrinsic_value_per_share:.2f} SEK**")

    if intrinsic_value_per_share > row["Price"]:
        st.success("💰 Aktien verkar undervärderad enligt DCF.")
    else:
        st.warning("📉 Aktien verkar övervärderad enligt DCF.")
else:
    st.info("Ingen giltig FreeCashflow-data för DCF-beräkning.")
