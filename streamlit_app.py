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


# --- Enkel DCF-beräkning på per-aktie-basis ---
if row["FreeCashflow"] > 0 and wacc and wacc > 0:
    fcf_total = row["FreeCashflow"]
    market_cap = row["MarketCap"]
    price = row["Price"]

    # Antal aktier (ungefär)
    shares_outstanding = market_cap / price if price > 0 else None

    if shares_outstanding and shares_outstanding > 0:
        # FCF per aktie
        fcf_per_share = fcf_total / shares_outstanding

        # Antaganden
        growth_rate = 0.03       # framtida FCF-tillväxt
        terminal_growth = 0.02   # evig tillväxt
        years = 5                # prognosperiod (år)

        # Prognostisera framtida kassaflöden per aktie
        fcfs = [fcf_per_share * ((1 + growth_rate) ** i) for i in range(1, years + 1)]
        discounted_fcfs = [fcf / ((1 + wacc) ** i) for i, fcf in enumerate(fcfs, start=1)]

        # Terminalvärde per aktie
        terminal_value = fcfs[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
        discounted_tv = terminal_value / ((1 + wacc) ** years)

        # Totalt intrinsic value per aktie
        intrinsic_value = sum(discounted_fcfs) + discounted_tv

        st.subheader("📈 Enkel DCF-värdering (per aktie)")
        st.write(f"Intrinsic Value (per aktie): **{intrinsic_value:.2f} SEK**")

        diff = (intrinsic_value - price) / price * 100
        if intrinsic_value > price:
            st.success(f"💰 Aktien verkar undervärderad med {diff:.1f}% enligt DCF.")
        else:
            st.warning(f"📉 Aktien verkar övervärderad med {abs(diff):.1f}% enligt DCF.")
    else:
        st.info("Ogiltig aktiekurs eller marknadsvärde för att beräkna antal aktier.")
else:
    st.info("Ingen giltig FreeCashflow-data för DCF-beräkning.")
