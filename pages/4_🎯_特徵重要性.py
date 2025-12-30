import streamlit as st
import plotly.express as px
from PIL import Image

from utils.bigquery_data import get_feature_importance
from utils.sidebar import render_sidebar

st.set_page_config(
    page_title="特徵重要性 - Netflix 預測系統",
    page_icon="🎯",
    layout="wide"
)

# Render shared sidebar
render_sidebar()

st.title("🎯 特徵重要性分析")
st.info("✅ 以下數據來自 XGBoost 模型訓練結果（真實資料）")
st.markdown("---")

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

# ========== 下架預測特徵重要性 ==========
st.subheader("📉 下架預測 - 關鍵影響因素")

st.write("根據 XGBoost 模型，以下是影響作品下架的關鍵決策因子（依重要性排序）：")

# 顯示下架預測特徵重要性圖片
try:
    churn_img = Image.open("assets/churn_feature_importance.png")
    st.image(
        churn_img,
        caption="下架預測模型 - 特徵重要性排序（XGBoost Importance Gain）",
        use_container_width=True
    )
except:
    st.warning("⚠️ 圖片載入失敗，請確認 assets/churn_feature_importance.png 存在")

# 解讀說明
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🎬 合約結構主導：**
    - Type（電影/影集）是最關鍵因素
    - 電影與影集授權期限差異大
    - Release Year 反映片齡與合約到期
    """)

with col2:
    st.markdown("""
    **📅 生命週期與熱度：**
    - Days Since Added 預測合約到期
    - Vote Count / Popularity 影響續約決策
    - 高熱度作品續約機率較高
    """)

st.info("""
💡 **模型洞察：** 下架風險主要由「合約類型 + 上架時長 + 市場熱度」決定。
版權團隊可優先監控「電影 + 老片 + 上架時間長」的作品，並根據市場熱度評估續約價值。
""")

st.markdown("---")
st.caption("📊 資料來源：BigQuery ML | 🤖 模型：XGBoost")