import streamlit as st
import pandas as pd

st.title('Valora 🇸🇪')

# --- Ladda in data ---
df = pd.read_csv('https://raw.githubusercontent.com/cb2cb/cb-machinelearning/refs/heads/master/fundamental_data.csv')
st.dataframe(df)

# --- Svensk WACC-funktion ---
def calc_wacc(
    market_cap,
    total_debt=None,
    cash=0,
    beta=1.0,
    interest_expense=None,
    tax_rate=0.20  # svensk bolagsskatt
):
    """
    Beräknar WACC (Weighted Average Cost of Capital)
    för svenska bolag.
    """

    # --- Svenska standardvärden ---
    risk_free = 0.025           # 10-årig statsobligation ≈ 2.5 %
    market_premium = 0.055      # svensk riskpremie ≈ 5.5 %
    re = risk_free + beta * market_premium  # kostnad för eget kapital (CAPM)

    # --- Kostnad för skulder ---
    if interest_expense is not None and total_debt and total_debt > 0:
        rd = interest_expense / total_debt
    else:
        rd = risk_free + 0.015   # schablon för kreditrisk

    # --- Kapitalstruktur ---
    E = market_cap
    D = total_debt if total_debt else 0
    V = E + D

    if V == 0:
        return None

    wacc = (E/V) * re + (D/V) * rd * (1 - tax_rate)
    return round(wacc, 4)

# --- Välj bolag ---
ticker = st.selectbox("Välj bolag (ticker):", df["Ticker"].unique())
row = df[df["Ticker"] == ticker].iloc[0]

# --- Uppskatta skulder baserat på Debt/Equity ---
if pd.notnull(row["Debt/Equity"]) and row["Debt/Equity"] > 0:
    total_debt = row["MarketCap"] * (row["Debt/Equity"] / 100)
else:
    total_debt = None

# --- Beräkna WACC ---
wacc = calc_wacc(
    market_cap=row["MarketCap"],
    total_debt=total_debt,
    beta=row["Beta"]
)

st.metric("Beräknad WACC", f"{wacc*100:.2f}%")

# --- Tolkning ---
if wacc:
    if wacc < 0.07:
        st.success("🟢 Låg kapitalkostnad – stabilt, moget bolag.")
    elif wacc < 0.10:
        st.info("🟡 Medelhög kapitalkostnad – balanserad risk.")
    else:
        st.warning("🔴 Hög kapitalkostnad – tillväxt eller hög risk.")



# --- Enkel DCF-beräkning baserad på FreeCashflow ---
if pd.notnull(row["FreeCashflow"]) and row["FreeCashflow"] > 0:
    fcf_now = row["FreeCashflow"]

    # Antaganden
    growth_rate = 0.03       # framtida årlig FCF-tillväxt
    terminal_growth = 0.02   # evig tillväxt
    years = 5                # prognosperiod (år)

    # Prognostisera framtida kassaflöden
    fcfs = [fcf_now * ((1 + growth_rate) ** i) for i in range(1, years + 1)]

    # Diskontera varje FCF
    discounted_fcfs = [fcf / ((1 + wacc) ** i) for i, fcf in enumerate(fcfs, start=1)]

    # Terminalvärde (värdet efter år 5)
    terminal_value = fcfs[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
    discounted_tv = terminal_value / ((1 + wacc) ** years)

    # Summera
    enterprise_value = sum(discounted_fcfs) + discounted_tv

    # Antag att MarketCap ≈ EquityValue
    intrinsic_value = enterprise_value / row["MarketCap"] * row["Price"]

    st.subheader("📈 Enkel DCF-värdering")
    st.write(f"Intrinsic Value (per aktie): **{intrinsic_value:.2f} SEK**")

    if intrinsic_value > row["Price"]:
        st.success("💰 Aktien verkar undervärderad enligt DCF.")
    else:
        st.warning("📉 Aktien verkar övervärderad enligt DCF.")
else:
    st.info("Ingen FreeCashflow-data tillgänglig för DCF-beräkning.")
