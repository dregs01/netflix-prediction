import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 匯入自訂功能
from utils.bigquery_data import (
    get_top10_predictions,
    get_model_performance
)

# ========== 設定 ==========
USE_REAL_DATA = True  # ✅ 預設使用真實資料

# ========== 頁面設定 ==========
st.set_page_config(
    page_title="🔥 預測 Top 10 爆紅作品",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 如果使用假資料，在最上方顯示警告
if not USE_REAL_DATA:
    st.error("⚠️ 警告：目前使用模擬資料展示，非真實預測結果！")

# Netflix 風格 CSS
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
    
    /* 標題樣式 */
    h1 {
        color: #141414;
    }
    
    /* 側邊欄樣式 */
    [data-testid="stSidebar"] {
        background-color: #141414;
    }
</style>
""", unsafe_allow_html=True)

# ========== 側邊欄 ==========
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg", width=200)
    st.markdown("---")
    
    if st.button("🔥 預測 Top 10 爆紅作品", use_container_width=True):
        st.switch_page("app.py")
    
    if st.button("🔍 作品搜尋", use_container_width=True):
        st.switch_page("pages/1_🔍_作品搜尋.py")
    
    if st.button("🌍 Google Trends", use_container_width=True):
        st.switch_page("pages/2_🌍_Google_Trends.py")
    
    if st.button("🎯 特徵重要性", use_container_width=True):
        st.switch_page("pages/3_🎯_特徵重要性.py")

    

# ========== 主標題 ==========
st.title("🎬 Netflix 作品爆紅預測系統")
st.markdown("---")

# ========== Top 10 爆紅作品榜單 ==========
st.header("🔥 預測 Top 10 爆紅作品（未來14天）")

if USE_REAL_DATA:
    st.info("💡 根據 XGBoost 模型預測，以下作品最有可能在未來 14 天內進入全球 Top 10 榜單")
else:
    st.warning("⚠️ 以下為模擬資料展示")

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
        st.warning("⚠️ 目前沒有預測資料，可能原因：")
        st.write("1. BigQuery 資料表尚未建立")
        st.write("2. 本週尚未執行預測")
        st.write("3. 資料庫連接問題")

else:
    # 假資料模式 - 明顯標示
    st.error("🚨 注意：目前使用模擬資料展示")
    st.warning("💡 這不是真實的預測結果，僅供功能展示")
    
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

# ========== 頁尾 ==========
st.markdown("---")
st.caption("📊 資料來源：Kaggle + Netflix Engagement Reports | 🤖 模型：BigQuery ML + Vertex AI")
st.caption("⚙️ 技術架構：Cloud Storage → BigQuery → Cloud Run → Streamlit")