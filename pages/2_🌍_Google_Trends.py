import streamlit as st

from utils.trends import display_trends_section
from utils.sidebar import render_sidebar

st.set_page_config(
    page_title="Google Trends - Netflix 預測系統",
    page_icon="🌍",
    layout="wide"
)

# Render shared sidebar
render_sidebar()

# 直接顯示 Google Trends 分析
display_trends_section()