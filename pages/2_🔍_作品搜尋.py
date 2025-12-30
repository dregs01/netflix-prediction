import streamlit as st
from utils.bigquery_data import get_all_titles, get_title_details, get_title_churn_prediction
from utils.sidebar import render_sidebar

st.set_page_config(
    page_title="作品搜尋 - Netflix 預測系統",
    page_icon="🔍",
    layout="wide"
)

# Render shared sidebar
render_sidebar()

st.title("🔍 查詢特定作品")
st.markdown("---")

# 載入所有作品名稱
all_titles = get_all_titles()

if all_titles:
    # 直接使用下拉選單（支援輸入篩選）
    selected_title = st.selectbox(
        "選擇作品（輸入關鍵字可快速篩選）",
        options=all_titles,
        index=None,
        placeholder="請輸入作品名稱..."
    )
    
    # 搜尋按鈕
    if st.button("🔍 查詢", type="primary", use_container_width=True):
        if selected_title:
            st.success(f"✅ 找到作品：{selected_title}")
            
            # 查詢詳細資訊
            with st.spinner("正在從 BigQuery 載入資料..."):
                details = get_title_details(selected_title)
                churn_prob = get_title_churn_prediction(selected_title)
            
            if details is not None:
                # ========== 基本資訊 ==========
                st.markdown("### 📋 詳細數據")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("類型", details.get('type', 'N/A'))
                    
                with col2:
                    st.metric("語言", details.get('language', 'N/A'))
                    
                with col3:
                    imdb_score = details.get('imdb_score', 0)
                    st.metric("IMDb 評分", f"{imdb_score}/10" if imdb_score else "無資料")
                    
                with col4:
                    weeks = details.get('weeks_in_top10', 0)
                    st.metric("Top 10 上榜週數", int(weeks) if weeks else 0)
                
                # ========== 第二排指標 ==========
                col5, col6, col7, col8 = st.columns(4)
                
                with col5:
                    st.metric("國家", details.get('country', 'N/A'))
                    
                with col6:
                    st.metric("發行年份", details.get('release_year', 'N/A'))
                    
                with col7:
                    tmdb_pop = details.get('tmdb_popularity', 0)
                    st.metric("TMDB 熱度", f"{tmdb_pop:.1f}" if tmdb_pop else "無資料")
                    
                with col8:
                    ranking = details.get('highest_ranking', 0)
                    if ranking and ranking > 0:
                        st.metric("最佳排名", f"#{int(ranking)}")
                    else:
                        st.metric("最佳排名", "未上榜")
                
                st.markdown("---")
                
                # ========== 預測指標 ==========
                st.markdown("### 🎯 作品資訊")
                
                pred_col1, pred_col2 = st.columns(2)
                
                with pred_col1:
                    # 經濟數據
                    st.markdown("#### 💰 經濟數據")
                    budget = details.get('budget', 0)
                    revenue = details.get('revenue', 0)
                    
                    if budget and budget > 0:
                        st.write(f"**預算：** ${budget:,.0f}")
                    else:
                        st.write("**預算：** 無資料")
                    
                    if revenue and revenue > 0:
                        st.write(f"**收益：** ${revenue:,.0f}")
                    else:
                        st.write("**收益：** 無資料")
                
                with pred_col2:
                    # 觀看數據
                    st.markdown("#### 📺 觀看數據")
                    
                    views_2023 = details.get('views_2023', 0)
                    views_2024 = details.get('views_2024', 0)
                    views_2025 = details.get('views_2025', 0)
                    
                    if views_2023 and views_2023 > 0:
                        st.write(f"**2023 觀看數：** {views_2023:,}")
                    else:
                        st.write("**2023 觀看數：** 無資料")
                    
                    if views_2024 and views_2024 > 0:
                        st.write(f"**2024 觀看數：** {views_2024:,}")
                    else:
                        st.write("**2024 觀看數：** 無資料")
                    
                    if views_2025 and views_2025 > 0:
                        st.write(f"**2025 觀看數：** {views_2025:,}")
                    else:
                        st.write("**2025 觀看數：** 無資料")
                
                st.markdown("---")
                
                # ========== 預測結果（並排顯示） ==========
                st.markdown("### 🔮 AI 預測分析")
                
                pred_col1, pred_col2 = st.columns(2)
                
                with pred_col1:
                    # 爆紅預測
                    st.markdown("#### 🔥 未來 14 天爆紅機率")
                    viral_prob = details.get('viral_probability_14d', 0)
                    
                    if viral_prob and viral_prob > 0:
                        viral_pct = viral_prob * 100
                        
                        # 根據機率顯示不同顏色
                        if viral_pct >= 10:
                            st.success(f"### 🔥 {viral_pct:.1f}%")
                            st.write("**高潛力作品**，建議優先推廣！")
                        elif viral_pct >= 5:
                            st.warning(f"### ⚡ {viral_pct:.1f}%")
                            st.write("**中等潛力**，可考慮配置部分資源")
                        else:
                            st.info(f"### 📊 {viral_pct:.1f}%")
                            st.write("**標準表現**")
                        
                        # 進度條
                        st.progress(min(viral_pct / 100, 1.0))
                    else:
                        st.info("### 📊 0%")
                        st.write("**無預測資料**")
                
                with pred_col2:
                    # 下架預測
                    st.markdown("#### 📉 未來 90 天下架風險")
                    
                    if churn_prob is not None:
                        churn_pct = churn_prob * 100
                        
                        # 根據風險顯示不同顏色
                        if churn_pct >= 70:
                            st.error(f"### 🔴 {churn_pct:.1f}%")
                            st.write("**高風險**，建議提前通知使用者或評估續約")
                        elif churn_pct >= 50:
                            st.warning(f"### 🟡 {churn_pct:.1f}%")
                            st.write("**中等風險**，密切監控")
                        else:
                            st.success(f"### 🟢 {churn_pct:.1f}%")
                            st.write("**低風險**，維持現狀")
                        
                        # 進度條
                        st.progress(min(churn_pct / 100, 1.0))
                    else:
                        st.info("### 📊 無資料")
                        st.write("**此作品無下架預測資料**")
                        st.caption("可能原因：新上架作品或資料不完整")
                
            else:
                st.error("❌ 找不到此作品的詳細資料")
                st.info("💡 請確認作品名稱是否正確，或嘗試使用完整英文名稱")
        else:
            st.warning("⚠️ 請先選擇或輸入作品名稱")

else:
    st.error("❌ 無法載入作品清單")
    st.info("請檢查 BigQuery 連接是否正常")

# ========== 頁尾 ==========
st.markdown("---")
st.caption("📊 資料來源：BigQuery ML | 🤖 模型：XGBoost (爆紅預測 + 下架預測)")