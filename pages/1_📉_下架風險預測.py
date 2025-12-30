import streamlit as st
import plotly.graph_objects as go

from utils.bigquery_data import get_top10_churn_predictions
from utils.sidebar import render_sidebar

st.set_page_config(
    page_title="下架風險預測 - Netflix 預測系統",
    page_icon="📉",
    layout="wide"
)

render_sidebar()

# ========== 標題 ==========
st.title("📉 作品下架風險預測")
st.markdown("---")

st.info("💡 根據 XGBoost 模型預測，以下是未來最有可能下架的 Top 10 作品")

# ========== 載入預測資料 ==========
with st.spinner("正在從 BigQuery 載入下架預測資料..."):
    churn_data = get_top10_churn_predictions()

if churn_data is not None and not churn_data.empty:
    # 準備顯示用的 DataFrame
    display_df = churn_data[['title', 'type', 'country', 'churn_probability']].copy()
    display_df.columns = ['作品名稱', '類型', '製作國家', '下架風險']
    display_df.insert(0, '排名', range(1, len(display_df) + 1))
    
    # 顯示表格
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "下架風險": st.column_config.ProgressColumn(
                "下架風險 (%)",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        }
    )
    
    # 視覺化
    fig = go.Figure(data=[
        go.Bar(
            x=display_df['下架風險'],
            y=display_df['作品名稱'],
            orientation='h',
            marker=dict(
                color=display_df['下架風險'],
                colorscale='OrRd',  # 橘紅色系（警告色）
                showscale=False
            ),
            text=[f"{x:.1f}%" for x in display_df['下架風險']],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title='Top 10 作品下架風險視覺化',
        xaxis_title='下架風險 (%)',
        yaxis_title='',
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 說明
    st.markdown("---")
    st.markdown("""
    ### 💡 如何使用這個預測？
    
    **對於高風險作品（>70%）：**
    - 📢 **提前通知使用者**：在下架前 14 天發送通知
    - 🎯 **加強推薦**：增加首頁曝光，讓更多人觀看
    - 💰 **評估續約**：分析是否值得續約
    
    **對於中風險作品（50-70%）：**
    - 👀 **密切監控**：追蹤觀看數據變化
    - 🤝 **談判準備**：準備續約談判資料
    
    **對於低風險作品（<50%）：**
    - ✅ **維持現狀**：繼續正常營運
    """)
    
else:
    st.warning("⚠️ 目前沒有下架預測資料")
    st.info("可能原因：")
    st.write("1. 模型尚未執行預測")
    st.write("2. 資料表暫時無法存取")
    st.write("3. 資料庫連接問題")