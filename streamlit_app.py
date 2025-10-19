import streamlit as st
import pandas as pd

st.title("Valora 🇸🇪")

# --- Ladda in data ---
df = pd.read_csv("https://raw.githubusercontent.com/cb2cb/cb-machinelearning/refs/heads/master/fundamental_data.csv")
st.dataframe(df)

# --- Välj bolag ---
ticker = st.selectbox("Välj bolag:", df["Ticker"].unique())
row = df[df["Ticker"] == ticker].iloc[0]

# --- Grundparametrar för modellen ---
discount_rate = 0.08       # 8 % diskonteringsränta
growth_rate = 0.03         # Årlig tillväxt i kassaflöde 3 %
terminal_growth = 0.02     # Terminal tillväxt 2 %
years = 5

# --- FCF per aktie ---
if row["Price"] > 0 and row["FreeCashflow"] > 0 and row["MarketCap"] > 0:
    shares = row["MarketCap"] / row["Price"]
    fcf_per_share = row["FreeCashflow"] / shares

    # Framtida FCF per aktie
    future_fcfs = [fcf_per_share * ((1 + growth_rate) ** t) for t in range(1, years + 1)]

    # Diskontera framtida kassaflöden
    discounted_fcfs = [fcf / ((1 + discount_rate) ** t) for t, fcf in enumerate(future_fcfs, start=1)]

    # Terminalvärde
    terminal_value = (future_fcfs[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    discounted_terminal = terminal_value / ((1 + discount_rate) ** years)

    # Summera allt
    intrinsic_value = sum(discounted_fcfs) + discounted_terminal

    # Resultat per aktie
    st.subheader("📈 Diskonteringsmodell (Intrinsic Value)")
    st.metric("Intrinsic Value (SEK)", f"{intrinsic_value:.2f}")
    diff = (intrinsic_value - row["Price"]) / row["Price"] * 100
    if diff > 0:
        st.success(f"💰 Undervärderad med {diff:.1f} %")
    else:
        st.warning(f"📉 Övervärderad med {abs(diff):.1f} %")
else:
    st.info("Otillräcklig data (FCF, Price eller MarketCap saknas).")
