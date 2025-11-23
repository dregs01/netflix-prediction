"""
Google Trends 相關功能
"""
import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import plotly.express as px

@st.cache_data(ttl=3600)  # 快取 1 小時
def get_netflix_trends(keywords=None):
    """
    取得 Netflix 作品的 Google Trends 資料
    
    參數:
        keywords: list, 要查詢的關鍵字列表
    
    回傳:
        DataFrame 或 None
    """
    if keywords is None:
        keywords = ['Stranger Things', 'Wednesday', 'Squid Game', 'The Crown', 'Bridgerton']
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload(keywords, timeframe='now 7-d', geo='')
        
        interest_over_time = pytrends.interest_over_time()
        
        if not interest_over_time.empty:
            return interest_over_time.drop('isPartial', axis=1)
        else:
            return None
    except Exception as e:
        st.error(f"Google Trends API 錯誤: {str(e)}")
        return None


@st.cache_data(ttl=1800)  # 快取 30 分鐘
def get_show_trend_score(show_name):
    """
    取得特定作品的 Google Trends 分數
    
    參數:
        show_name: str, 作品名稱
    
    回傳:
        float, 平均分數 (0-100)
    """
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([show_name], timeframe='now 7-d', geo='')
        
        interest_over_time = pytrends.interest_over_time()
        
        if not interest_over_time.empty:
            avg_score = interest_over_time[show_name].mean()
            return round(avg_score, 1)
        else:
            return 0
    except Exception as e:
        return 0


def display_trends_section():
    """
    顯示 Google Trends 分析區塊（完整 UI）
    """
    st.markdown("---")
    st.header("🌍 Google Trends 全球討論度分析")
    
    tab1, tab2 = st.tabs(["📊 熱門作品排行", "📈 自訂關鍵字查詢"])
    
    with tab1:
        with st.spinner("正在從 Google Trends 取得最新資料..."):
            trends_data = get_netflix_trends()
        
        if trends_data is not None:
            # 最新排名
            latest_scores = trends_data.iloc[-1].sort_values(ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 當前討論度排行")
                
                ranking_df = pd.DataFrame({
                    '排名': range(1, len(latest_scores) + 1),
                    '作品': latest_scores.index,
                    '討論度': latest_scores.values
                })
                
                st.dataframe(
                    ranking_df,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "討論度": st.column_config.ProgressColumn(
                            "討論度指數",
                            format="%d",
                            min_value=0,
                            max_value=100,
                        ),
                    }
                )
            
            with col2:
                st.subheader("📈 7 天趨勢變化")
                
                fig = px.line(
                    trends_data,
                    title='過去 7 天討論度趨勢',
                    labels={'value': '討論度指數', 'date': '日期'}
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            
            # 詳細趨勢圖
            st.subheader("🔥 熱度趨勢比較")
            
            selected_shows = st.multiselect(
                "選擇要比較的作品",
                options=trends_data.columns.tolist(),
                default=trends_data.columns.tolist()[:3]
            )
            
            if selected_shows:
                fig2 = px.area(
                    trends_data[selected_shows],
                    title='作品討論度比較',
                    labels={'value': '討論度指數', 'date': '日期'}
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("⚠️ 無法取得 Google Trends 資料，請稍後再試")
    
    with tab2:
        st.subheader("查詢特定作品的搜尋熱度")
        
        custom_keyword = st.text_input("輸入作品名稱（英文）", "Stranger Things")
        timeframe = st.selectbox(
            "選擇時間範圍",
            ["now 7-d", "today 1-m", "today 3-m", "today 12-m"],
            format_func=lambda x: {
                "now 7-d": "過去 7 天",
                "today 1-m": "過去 1 個月",
                "today 3-m": "過去 3 個月",
                "today 12-m": "過去 12 個月"
            }[x]
        )
        
        if st.button("🔍 查詢", type="primary"):
            with st.spinner("查詢中..."):
                try:
                    pytrends = TrendReq(hl='en-US', tz=360)
                    pytrends.build_payload([custom_keyword], timeframe=timeframe, geo='')
                    
                    data = pytrends.interest_over_time()
                    
                    if not data.empty:
                        fig = px.line(
                            data[custom_keyword],
                            title=f'{custom_keyword} 搜尋趨勢',
                            labels={'value': '討論度指數', 'date': '日期'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        avg_score = data[custom_keyword].mean()
                        max_score = data[custom_keyword].max()
                        
                        col1, col2 = st.columns(2)
                        col1.metric("平均搜尋熱度", f"{avg_score:.1f}/100")
                        col2.metric("最高搜尋熱度", f"{max_score}/100")
                    else:
                        st.warning("❌ 查無資料，請確認作品名稱是否正確")
                except Exception as e:
                    st.error(f"❌ 查詢失敗：{str(e)}")
    
    st.info("💡 資料來源：Google Trends API | 更新頻率：每小時")