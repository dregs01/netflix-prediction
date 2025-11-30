import streamlit as st


def _render_css():
    st.markdown("""
    <style>
        /* 隱藏預設的頁面導航 */
        [data-testid="stSidebarNav"] {
            display: none;
        }
        /* Netflix 紅色主題 */
        .stButton>button {
            background-color: #E50914;
            color: white;
            border-radius: 4px;
            border: none;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #B20710;
        }
        /* 側邊欄樣式 */
        [data-testid="stSidebar"] {
            background-color: #141414;
        }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the custom Netflix-style sidebar for all pages."""
    _render_css()

    with st.sidebar:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg",
            width=200
        )
        st.markdown("---")

        if st.button("🔥 預測 Top 10 爆紅作品", use_container_width=True):
            try:
                st.switch_page("app.py")
            except Exception:
                # fallback: do nothing if switch_page not available
                pass

        if st.button("🔍 作品搜尋", use_container_width=True):
            try:
                st.switch_page("pages/1_🔍_作品搜尋.py")
            except Exception:
                pass

        if st.button("🌍 Google Trends", use_container_width=True):
            try:
                st.switch_page("pages/2_🌍_Google_Trends.py")
            except Exception:
                pass

        if st.button("🎯 特徵重要性", use_container_width=True):
            try:
                st.switch_page("pages/3_🎯_特徵重要性.py")
            except Exception:
                pass
