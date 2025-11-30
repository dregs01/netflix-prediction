import streamlit as st

from utils.trends import display_trends_section

st.set_page_config(
    page_title="Google Trends - Netflix 預測系統",
    page_icon="🌍",
    layout="wide"
)

# 直接顯示 Google Trends 分析
display_trends_section()