import streamlit as st
import pandas as pd

st.title("Valora")

# Option 1: Ladda fil via filuppladdare
uploaded_file = st.file_uploader("Ladda CSV-fil med data", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    # Alternativt: använd statiskt filnamn (om du har filen lokalt)
    df = pd.read_csv("fundamental_data.csv")  # Ändra till rätt filväg

st.dataframe(df)

# --- Välj bolag ---
ticker = st.selectbox("Välj bolag:", df["Ticker"].unique())
row = df[df["Ticker"] == ticker].iloc[0]

# --- Grundparametrar för modellen ---
discount_rate = 0.08       # 8 % diskonteringsränta
terminal_growth = 0.02     # Terminal tillväxt 2 %
years = 5

def intrinsic_value_dcf(fcf, cagr_pct, discount_rate, years, terminal_growth):
    cagr = cagr_pct / 100  # omvandla procent till decimalt
    future_cf = [fcf * ((1 + cagr) ** t) for t in range(1, years + 1)]
    discounted_cf = [cf / ((1 + discount_rate) ** t) for t, cf in enumerate(future_cf, 1)]
    terminal_value = future_cf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    discounted_terminal = terminal_value / ((1 + discount_rate) ** years)
    return sum(discounted_cf) + discounted_terminal

# --- FCF per aktie ---
if row["Price"] > 0 and row["FreeCashflow"] > 0 and row["MarketCap"] > 0:
    shares = row["MarketCap"] / row["Price"]
    fcf_per_share = row["FreeCashflow"] / shares

    # Använd kolumnen "TwoYearCAGR_orelse3%" som procent
    cagr_pct = row.get("TwoYearCAGR_orelse3%", 3)  # default 3% om saknas

    # Kontrollera att cagr är inom rimliga värden
    if cagr_pct <= 0 or cagr_pct > 30:
        cagr_pct = 3

    intrinsic_val = intrinsic_value_dcf(fcf_per_share, cagr_pct, discount_rate, years, terminal_growth)

    st.subheader("📈 Diskonteringsmodell (Intrinsic Value)")
    st.metric("Intrinsic Value (SEK)", f"{intrinsic_val:.2f}")
    diff = (intrinsic_val - row["Price"]) / row["Price"] * 100
    if diff > 0:
        st.success(f"💰 Undervärderad med {diff:.1f} %")
    else:
        st.warning(f"📉 Övervärderad med {abs(diff):.1f} %")
else:
    st.info("Otillräcklig data (FCF, Price eller MarketCap saknas).")
