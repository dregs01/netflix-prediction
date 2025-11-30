"""
Google Trends 相關功能
"""
import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import plotly.express as px

# 從預測資料取得 top 項目
from utils.bigquery_data import get_top10_predictions

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

        # Google Trends / pytrends accepts up to 5 keywords per payload.
        # 如果關鍵字超過 5 個，分批查詢並以第一個關鍵字作為 anchor 對齊縮放後合併。
        if len(keywords) <= 5:
            pytrends.build_payload(keywords, timeframe='now 7-d', geo='')
            interest_over_time = pytrends.interest_over_time()
            if not interest_over_time.empty:
                return interest_over_time.drop(columns=['isPartial'], errors='ignore')
            return None

        # 超過 5 個關鍵字的處理
        anchor = keywords[0]
        # 第一批使用前 5 個關鍵字
        batches = []
        batches.append(keywords[:5])
        idx = 5
        # 後續每批包含 anchor + 最多 4 個新關鍵字
        while idx < len(keywords):
            batch = [anchor] + keywords[idx:idx+4]
            batches.append(batch)
            idx += 4

        df_total = None
        baseline_anchor_series = None

        for i, batch in enumerate(batches):
            pytrends.build_payload(batch, timeframe='now 7-d', geo='')
            df = pytrends.interest_over_time()
            if df is None or df.empty:
                continue
            df = df.drop(columns=['isPartial'], errors='ignore')

            if i == 0:
                df_total = df.copy()
                # baseline anchor series
                if anchor in df_total.columns:
                    baseline_anchor_series = df_total[anchor].astype(float)
            else:
                # 對齊並縮放：以 anchor 為基準
                if anchor not in df.columns or baseline_anchor_series is None:
                    # 無法以 anchor 對齊，跳過此批
                    continue
                batch_anchor = df[anchor].astype(float)
                # 避免除以 0
                if batch_anchor.mean() == 0:
                    scale = 0
                else:
                    scale = baseline_anchor_series.mean() / batch_anchor.mean()

                # 進行縮放並移除 anchor（避免重複欄位）
                df_scaled = df.multiply(scale)
                df_scaled = df_scaled.drop(columns=[anchor], errors='ignore')

                # 合併至總表（以時間 index 對齊）
                df_total = pd.concat([df_total, df_scaled], axis=1)

        if df_total is None or df_total.empty:
            return None

        # 最後依原始 keywords 的順序排序欄位，缺的欄位補 0
        # 使用 astype(float) 保證數值型別一致
        for col in df_total.columns:
            df_total[col] = pd.to_numeric(df_total[col], errors='coerce').fillna(0)

        df_total = df_total.reindex(columns=keywords, fill_value=0)
        return df_total

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
        # 僅使用 Top Predictions，固定取前 5 名作為關鍵字
        top_n = 5
        with st.spinner('正在載入預測結果...'):
            pred_df = get_top10_predictions()

        keywords = None
        if pred_df is not None and not pred_df.empty:
            keywords = pred_df['title'].astype(str).head(top_n).tolist()
        else:
            st.warning('⚠️ 無法載入預測結果，改用預設熱門清單（前 5 名）')
            # fallback: 使用內建列表的前 5 名
            default_list = ['Stranger Things', 'Wednesday', 'Squid Game', 'The Crown', 'Bridgerton',
                            'Black Mirror', 'Money Heist', 'Ozark', 'The Witcher', 'Lucifer']
            keywords = default_list[:top_n]

        with st.spinner("正在從 Google Trends 取得最新資料（前 5 名）..."):
            trends_data = get_netflix_trends(keywords=keywords)

        if trends_data is not None:
            # 只顯示前 5 名（keywords 已限制為 top_n）
            latest_scores = trends_data.iloc[-1].reindex(keywords).fillna(0).sort_values(ascending=False)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 當前討論度排行（前 5 名）")

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
                st.subheader("📈 7 天趨勢變化（前 10 名）")

                # 僅繪製前 10 名的趨勢線
                fig = px.line(
                    trends_data[keywords],
                    title='過去 7 天討論度趨勢（前 5 名）',
                    labels={'value': '討論度指數', 'date': '日期'}
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

            # 詳細趨勢圖（僅前 10 名）
            st.subheader("🔥 熱度趨勢比較（前 5 名）")

            selected_shows = st.multiselect(
                "選擇要比較的作品（最多前 5 名）",
                options=keywords,
                default=keywords[:3]
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