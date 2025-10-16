import streamlit as st
import pandas as pd

st.title('🦉Valora')

df = pd.read_csv('https://raw.githubusercontent.com/cb2cb/cb-machinelearning/refs/heads/master/fundamental_data.csv')
df
