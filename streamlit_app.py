import streamlit as st
import pandas as pd

st.title('Valora')


# --- Ladda in data ---
df = pd.read_csv('https://raw.githubusercontent.com/cb2cb/cb-machinelearning/refs/heads/master/fundamental_data.csv')
df


# --- Funktion för att beräkna WACC ---
def calc_wacc(
    market_cap,
    total_debt,
    cash,
    beta,
    country="Sweden",
    interest_expense=None,
    tax_rate=None
):
    """
    Beräknar WACC (Weighted Average Cost of Capital) för nordiska och amerikanska bolag.
    """

    rf_map = {
        "Sweden": 0.025,
        "Norway": 0.03,
        "Finland": 0.027,
        "Denmark": 0.024,
        "USA": 0.045
    }
    rf = rf_map.get(country, 0.03)

    market_premium = 0.055 if country in ["Sweden", "Norway", "Finland", "Denmark"] else 0.05
    re = rf + beta * market_premium

    if interest_expense is not None and total_debt > 0:
        rd = interest_expense / total_debt
    else:
        rd = rf + 0.015

    default_tax = {
        "Sweden": 0.20,
        "Norway": 0.22,
        "Finland": 0.20,
        "Denmark": 0.22,
        "USA": 0.21
    }
    T = tax_rate if tax_rate is not None else default_tax.get(country, 0.21)

    E = market_cap
    D = max(total_debt - cash, 0)
    V = E + D

    if V == 0:
        return None

    wacc = (E/V) * re + (D/V) * rd * (1 - T)
    return round(wacc, 4)

# --- Funktion för att välja bolag och se WACC ---
company = st.selectbox("Välj bolag:", df["Name"].unique())

row = df[df["Name"] == company].iloc[0]

wacc = calc_wacc(
    market_cap=row["MarketCap"],
    total_debt=row["TotalDebt"],
    cash=row["Cash"],
    beta=row["Beta"],
    country=row["Country"]
)

st.metric("Beräknad WACC", f"{wacc*100:.2f}%")

