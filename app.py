import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 匯入自訂功能
from utils.trends import display_trends_section, get_show_trend_score
from utils.bigquery_data import (
    get_top10_predictions,
    get_all_titles,
    get_title_details,
    get_feature_importance,
    get_model_performance,
    test_connection
)

# 設定：是否使用真實資料
USE_REAL_DATA = True  # 改成 True 使用 BigQuery 資料

# ========== 頁面設定 ==========
st.set_page_config(
    page_title="Netflix 爆紅預測系統",
    page_icon="🎬",
    layout="wide"
)

# ========== 標題 ==========
st.title("🎬 Netflix 作品爆紅預測系統")
st.markdown("---")
st.write("協助 Netflix 行銷團隊預測作品是否會爆紅，並制定宣傳策略")

# ========== 側邊欄：輸入作品資訊 ==========
st.sidebar.header("📝 輸入作品資訊")

# 基本資訊
title = st.sidebar.text_input("作品名稱", "Stranger Things")
type_ = st.sidebar.selectbox("作品類型", ["TV Show", "Movie"])

# 類別（多選）
genre = st.sidebar.multiselect(
    "作品類別",
    ["Action", "Drama", "Comedy", "Horror", "Sci-Fi", "Romance", "Thriller", "Documentary"],
    default=["Sci-Fi", "Drama"]
)

# 製作資訊
country = st.sidebar.selectbox(
    "製作國家",
    ["US", "UK", "KR", "JP", "IN", "ES", "FR", "Other"]
)

is_original = st.sidebar.checkbox("Netflix Original", value=True)

# 數值資訊
cast_count = st.sidebar.slider("演員數量", 1, 30, 10)
director_count = st.sidebar.slider("導演數量", 1, 5, 1)

if type_ == "Movie":
    duration = st.sidebar.number_input("時長（分鐘）", 30, 300, 120)
else:
    duration = st.sidebar.number_input("季數", 1, 10, 2)

imdb_score = st.sidebar.slider("IMDb 分數", 1.0, 10.0, 7.5, 0.1)

# 預測按鈕
st.sidebar.markdown("---")
predict_button = st.sidebar.button("🔮 開始預測", type="primary", use_container_width=True)

# ========== 主頁面 ==========
if predict_button:
    # 顯示載入動畫
    with st.spinner("正在分析作品特徵..."):
        import time
        time.sleep(1)  # 模擬 API 呼叫
    
    # ========== 假的預測結果 ==========
    # 根據輸入的特徵計算假的機率（讓它看起來合理）
    viral_prob = 0.5 + (imdb_score / 20) + (0.1 if is_original else 0) + (len(genre) * 0.05)
    viral_prob = min(viral_prob, 0.95)  # 最高 95%
    
    removal_prob = 0.4 - (imdb_score / 25) - (0.15 if is_original else 0)
    removal_prob = max(removal_prob, 0.05)  # 最低 5%
    
    # ========== 顯示結果 ==========
    st.success("✅ 預測完成！")
    
    # 分成兩欄
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 預測結果")
        
        # 爆紅機率（大數字顯示）
        st.metric(
            "爆紅機率",
            f"{viral_prob*100:.1f}%",
            delta="高機率" if viral_prob > 0.7 else ("中等" if viral_prob > 0.4 else "低機率")
        )
        
        # 進度條視覺化
        st.progress(viral_prob)
        
        # 下架風險
        st.metric(
            "下架風險",
            f"{removal_prob*100:.1f}%",
            delta="低風險" if removal_prob < 0.3 else ("中等" if removal_prob < 0.6 else "高風險"),
            delta_color="inverse"
        )
        
        st.progress(removal_prob)
        
        # 行銷建議
        st.markdown("### 💡 行銷建議")
        if viral_prob > 0.7:
            st.success("✅ **強烈推薦**：值得大力宣傳推廣，投入主要行銷資源！")
        elif viral_prob > 0.4:
            st.warning("⚠️ **適度投入**：可以配置中等行銷預算，觀察初期表現。")
        else:
            st.error("❌ **謹慎評估**：爆紅機率較低，建議降低行銷預算或調整策略。")
    
    with col2:
        st.subheader("🎯 特徵重要性分析")
        
        # 假的特徵重要性數據
        importance_data = pd.DataFrame({
            '特徵': ['IMDb分數', 'Netflix Original', '作品類別', '演員數量', '製作國家', '導演數量'],
            '重要性': [0.35, 0.25, 0.18, 0.12, 0.07, 0.03]
        })
        
        # 橫向條形圖
        fig = px.bar(
            importance_data,
            x='重要性',
            y='特徵',
            orientation='h',
            title='影響爆紅的關鍵因素',
            color='重要性',
            color_continuous_scale='Reds'
        )
        fig.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)
        
        # 額外說明
        st.info("""
        **解讀說明：**
        - IMDb 分數是最重要的指標
        - Netflix Original 標記會顯著提升爆紅率
        - 作品類別的多樣性也有正向影響
        """)
    
    # ========== 作品資訊摘要 ==========
    st.markdown("---")
    st.subheader("📋 作品資訊摘要")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("作品名稱", title)
    col2.metric("類型", type_)
    col3.metric("製作國家", country)
    col4.metric("類別", ", ".join(genre) if genre else "未選擇")

else:
    # ========== 初始頁面（未點預測時） ==========
    st.info("👈 請在左側輸入作品資訊，然後點擊「開始預測」按鈕")
    
    # 顯示範例
    st.subheader("📺 系統功能")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🎯 爆紅預測
        - 預測作品爆紅機率
        - 分析關鍵影響因素
        - 提供數據支持決策
        """)
    
    with col2:
        st.markdown("""
        ### 📊 風險評估
        - 評估下架風險
        - 預警低表現作品
        - 優化內容策略
        """)
    
    with col3:
        st.markdown("""
        ### 💡 行銷建議
        - 即時策略建議
        - 預算分配參考
        - 提升 ROI
        """)
# ========== 作品搜尋功能 ==========
st.markdown("---")
st.header("🔍 查詢特定作品")

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
                
                st.markdown("**🔮 爆紅預測**")
                viral = title_info.get('future_viral_14d')
                if viral == 1:
                    st.success("✅ 預測會爆紅（未來 14 天進入 Top 10）")
                elif viral == 0:
                    st.warning("⚠️ 預測不會爆紅")
                else:
                    st.info("ℹ️ 資料不足，無法判定")
        else:
            st.error("❌ 查無此作品資料")
else:
    st.info("🔧 作品搜尋功能需要啟用 BigQuery 連接（USE_REAL_DATA = True）")
# ========== Top 10 爆紅作品榜單 ==========
st.markdown("---")
st.header("🔥 預測 Top 10 爆紅作品（未來 14 天）")

st.info("💡 根據 XGBoost 模型預測，以下作品最有可能在未來 14 天內進入全球 Top 10 榜單")

if USE_REAL_DATA:
    with st.spinner("正在從 BigQuery 載入本週預測資料..."):
        top10_data = get_top10_predictions()
    
    if top10_data is not None and not top10_data.empty:
        # 準備顯示用的 DataFrame
        display_df = top10_data[['title', 'type', 'country', 'viral_probability']].copy()
        display_df.columns = ['作品名稱', '類型', '製作國家', '爆紅機率']
        display_df.insert(0, '排名', range(1, len(display_df) + 1))
        
        # 顯示表格
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "爆紅機率": st.column_config.ProgressColumn(
                    "爆紅機率 (%)",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            }
        )
        
        # 視覺化
        fig = go.Figure(data=[
            go.Bar(
                x=display_df['爆紅機率'],
                y=display_df['作品名稱'],
                orientation='h',
                marker=dict(
                    color=display_df['爆紅機率'],
                    colorscale='Reds',
                    showscale=False
                ),
                text=[f"{x:.1f}%" for x in display_df['爆紅機率']],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title='Top 10 作品爆紅機率視覺化',
            xaxis_title='爆紅機率 (%)',
            yaxis_title='',
            height=400,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示模型資訊
        with st.expander("📊 模型效能指標"):
            performance = get_model_performance()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🥇 XGBoost (主要模型)")
                st.metric("ROC-AUC", f"{performance['XGBoost']['roc_auc']:.4f}")
                st.metric("Accuracy", f"{performance['XGBoost']['accuracy']:.4f}")
                st.metric("Precision", f"{performance['XGBoost']['precision']:.3f}")
                st.metric("Recall", f"{performance['XGBoost']['recall']:.4f}")
            
            with col2:
                st.subheader("📊 Logistic Regression (基準)")
                st.metric("ROC-AUC", f"{performance['Logistic_Regression']['roc_auc']:.4f}")
                st.metric("Accuracy", f"{performance['Logistic_Regression']['accuracy']:.4f}")
                st.metric("Precision", f"{performance['Logistic_Regression']['precision']:.4f}")
                st.metric("Recall", f"{performance['Logistic_Regression']['recall']:.4f}")
            
            st.markdown("---")
            st.caption("💡 XGBoost 模型在 ROC-AUC 和 Precision 上表現優異，是我們的主要預測模型")
    else:
        st.warning("⚠️ 目前沒有預測資料，可能是：")
        st.write("1. BigQuery 資料表尚未建立")
        st.write("2. 本週尚未執行預測")
        st.write("3. 資料庫連接問題")
        
        # 顯示假資料作為示範
        st.info("🔧 以下顯示模擬資料作為介面展示")
        
        mock_data = pd.DataFrame({
            '排名': range(1, 11),
            '作品名稱': [
                'Stranger Things S5', 'Wednesday S2', 'The Crown S7',
                'Squid Game S3', 'Bridgerton S4', 'Money Heist: Korea',
                'The Witcher S4', 'You S5', 'Ozark: The Return', 'Dark Desire S3'
            ],
            '類型': ['TV Show'] * 10,
            '製作國家': ['US', 'US', 'UK', 'KR', 'US', 'KR', 'US', 'US', 'US', 'MX'],
            '爆紅機率': [95.2, 92.8, 89.5, 87.1, 85.3, 83.0, 81.2, 79.4, 77.6, 75.8]
        })
        
        st.dataframe(
            mock_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "爆紅機率": st.column_config.ProgressColumn(
                    "爆紅機率 (%)",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            }
        )
else:
    # 使用假資料（開發模式）
    st.info("🔧 目前使用模擬資料進行展示")
    
    mock_data = pd.DataFrame({
        '排名': range(1, 11),
        '作品名稱': [
            'Stranger Things S5', 'Wednesday S2', 'The Crown S7',
            'Squid Game S3', 'Bridgerton S4', 'Money Heist: Korea',
            'The Witcher S4', 'You S5', 'Ozark: The Return', 'Dark Desire S3'
        ],
        '類型': ['TV Show'] * 10,
        '製作國家': ['US', 'US', 'UK', 'KR', 'US', 'KR', 'US', 'US', 'US', 'MX'],
        '爆紅機率': [95.2, 92.8, 89.5, 87.1, 85.3, 83.0, 81.2, 79.4, 77.6, 75.8]
    })
    
    st.dataframe(
        mock_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "爆紅機率": st.column_config.ProgressColumn(
                "爆紅機率 (%)",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        }
    )
# ========== Feature Importance ==========
st.markdown("---")
st.header("🎯 特徵重要性分析")

st.write("根據 XGBoost 模型，以下是影響作品爆紅的關鍵因素（依重要性排序）：")

importance_df = get_feature_importance()

# 視覺化
fig = px.bar(
    importance_df,
    x='importance',
    y='feature_zh',
    orientation='h',
    title='XGBoost Feature Importance (by Gain)',
    color='importance',
    color_continuous_scale='Purples',
    labels={'importance': 'Importance Gain', 'feature_zh': '特徵'}
)

fig.update_layout(
    showlegend=False,
    height=500,
    yaxis={'categoryorder': 'total ascending'}
)

st.plotly_chart(fig, use_container_width=True)

# 解讀說明
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **💰 經濟指標最重要：**
    - 票房收益是最強預測因子
    - 製作預算也有顯著影響
    - 高投入通常帶來高回報
    """)

with col2:
    st.markdown("""
    **📊 社群參與度關鍵：**
    - TMDB 投票數反映討論熱度
    - 發行年份影響受眾偏好
    - 近期作品更容易受關注
    """)

st.info("""
💡 **模型洞察：** 成功的 Netflix 作品通常具備「高預算投入 + 強大社群討論度 + 優質內容評分」的組合。
行銷團隊可以優先推廣同時滿足這三個條件的作品。
""")
# ========== Google Trends 分析 ==========
display_trends_section()

# ========== 頁尾 ==========
st.markdown("---")
st.caption("📊 資料來源：Kaggle + Netflix Engagement Reports | 🤖 模型：BigQuery ML + Vertex AI")
st.caption("⚙️ 技術架構：Cloud Storage → BigQuery → Cloud Run → Streamlit")