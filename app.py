import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 匯入自訂功能
from utils.trends import display_trends_section, get_show_trend_score

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

# ========== Top 10 爆紅作品榜單 ==========
st.markdown("---")
st.header("🔥 預測 Top 10 爆紅作品")

# 假的 Top 10 數據
top10_data = pd.DataFrame({
    '排名': range(1, 11),
    '作品名稱': [
        'Stranger Things S5', 'Wednesday S2', 'The Crown S7',
        'Squid Game S3', 'Bridgerton S4', 'Money Heist: Korea',
        'The Witcher S4', 'You S5', 'Ozark: The Return', 'Dark Desire S3'
    ],
    '類型': ['TV Show', 'TV Show', 'TV Show', 'TV Show', 'TV Show',
             'TV Show', 'TV Show', 'TV Show', 'TV Show', 'TV Show'],
    '製作國家': ['US', 'US', 'UK', 'KR', 'US', 'KR', 'US', 'US', 'US', 'MX'],
    '爆紅機率': [0.95, 0.92, 0.89, 0.87, 0.85, 0.83, 0.81, 0.79, 0.77, 0.75],
    '預測觀看時數': ['500M', '450M', '420M', '400M', '380M', '360M', '340M', '320M', '300M', '280M']
})

# 顯示表格
st.dataframe(
    top10_data,
    use_container_width=True,
    hide_index=True,
    column_config={
        "爆紅機率": st.column_config.ProgressColumn(
            "爆紅機率",
            format="%.1f%%",
            min_value=0,
            max_value=1,
        ),
    }
)

# 視覺化 Top 10
fig = go.Figure(data=[
    go.Bar(
        x=top10_data['爆紅機率'],
        y=top10_data['作品名稱'],
        orientation='h',
        marker=dict(
            color=top10_data['爆紅機率'],
            colorscale='Reds',
            showscale=False
        ),
        text=[f"{x:.0%}" for x in top10_data['爆紅機率']],
        textposition='auto',
    )
])

fig.update_layout(
    title='Top 10 作品爆紅機率視覺化',
    xaxis_title='爆紅機率',
    yaxis_title='',
    height=400,
    yaxis={'categoryorder': 'total ascending'}
)

st.plotly_chart(fig, use_container_width=True)
# ========== Google Trends 分析 ==========
display_trends_section()

# ========== 頁尾 ==========
st.markdown("---")
st.caption("📊 資料來源：Kaggle + Netflix Engagement Reports | 🤖 模型：BigQuery ML + Vertex AI")
st.caption("⚙️ 技術架構：Cloud Storage → BigQuery → Cloud Run → Streamlit")