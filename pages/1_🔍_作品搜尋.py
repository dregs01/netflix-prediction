import streamlit as st
import pandas as pd

from utils.bigquery_data import get_all_titles, get_title_details, get_title_viral_rate
from utils.sidebar import render_sidebar

# ========== 設定 ==========
USE_REAL_DATA = True  # ✅ 預設使用真實資料

st.set_page_config(
    page_title="作品搜尋 - Netflix 預測系統",
    page_icon="🔍",
    layout="wide"
)

# Render shared sidebar
render_sidebar()

# 如果使用假資料，顯示警告
if not USE_REAL_DATA:
    st.error("⚠️ 警告：目前使用模擬資料展示，非真實資料！")

# ========== 標題 ==========
st.title("🔍 查詢特定作品")
st.markdown("---")

if USE_REAL_DATA:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.spinner("載入作品列表..."):
            all_titles = get_all_titles()
        
        if all_titles:
            selected_title = st.selectbox(
                "選擇或搜尋作品（輸入英文名稱）",
                options=all_titles,
                index=0
            )
        else:
            st.warning("⚠️ 無法載入作品列表")
            selected_title = None
    
    with col2:
        st.write("")
        st.write("")
        search_button = st.button("🔍 查詢", type="primary", use_container_width=True)
    
    if search_button and selected_title:
        with st.spinner(f"正在查詢《{selected_title}》..."):
            title_info = get_title_details(selected_title)
        
        if title_info:
            st.success(f"✅ 找到作品：{selected_title}")
            
            # 基本資訊
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("類型", title_info.get('type', 'N/A'))
                st.metric("國家", title_info.get('country', 'N/A'))
            
            with col2:
                st.metric("語言", title_info.get('language', 'N/A'))
                st.metric("發行年份", title_info.get('release_year', 'N/A'))
            
            with col3:
                imdb = title_info.get('imdb_rating', 0)
                st.metric("IMDb 評分", f"{imdb:.1f}/10" if imdb else 'N/A')
                tmdb_pop = title_info.get('tmdb_popularity', 0)
                st.metric("TMDB 熱度", f"{tmdb_pop:.1f}" if tmdb_pop else 'N/A')
            
            with col4:
                weeks = title_info.get('weeks_on_top10', 0)
                st.metric("Top 10 上榜週數", weeks if weeks else '未上榜')
                best = title_info.get('best_rank', 0)
                st.metric("最佳排名", f"#{best}" if best and best > 0 else '未上榜')
            
            # 詳細資訊
            st.markdown("---")
            st.subheader("📊 詳細數據")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**💰 經濟數據**")
                budget = title_info.get('budget', 0)
                revenue = title_info.get('revenue', 0)
                st.write(f"- 預算：${budget:,}" if budget else "- 預算：無資料")
                st.write(f"- 收益：${revenue:,}" if revenue else "- 收益：無資料")
                
                st.markdown("**📺 觀看數據**")
                views_23 = title_info.get('views_2023', 0)
                views_24 = title_info.get('views_2024', 0)
                views_25 = title_info.get('views_2025', 0)
                st.write(f"- 2023 觀看數：{views_23:,}" if views_23 else "- 2023：無資料")
                st.write(f"- 2024 觀看數：{views_24:,}" if views_24 else "- 2024：無資料")
                st.write(f"- 2025 觀看數：{views_25:,}" if views_25 else "- 2025：無資料")
            
            with col2:
                st.markdown("**🎭 作品資訊**")
                genres = title_info.get('genres', 'N/A')
                st.write(f"- 類別：{genres}")
                date_added = title_info.get('date_added', 'N/A')
                st.write(f"- 上架日期：{date_added}")
                
                # 取得爆紅率
                viral_rate = get_title_viral_rate(selected_title)
                if viral_rate is not None:
                    st.write(f"- 未來14天爆紅率：{viral_rate:.1f}%")
                else:
                    st.write("- 未來14天爆紅率：無預測資料")
        else:
            st.error("❌ 查無此作品資料")
else:
    # 假資料模式
    st.error("🚨 注意：目前使用模擬資料展示")
    st.warning("💡 作品搜尋功能需要啟用 BigQuery 連接才能使用真實資料")
    
    st.info("請將 `USE_REAL_DATA` 設定為 `True` 以使用真實資料")