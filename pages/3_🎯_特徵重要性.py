import streamlit as st
import plotly.express as px

from utils.bigquery_data import get_feature_importance

st.set_page_config(
    page_title="特徵重要性 - Netflix 預測系統",
    page_icon="🎯",
    layout="wide"
)

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