"""
BigQuery 資料讀取功能 - Netflix 爆紅預測系統
"""
from google.cloud import bigquery
import pandas as pd
import streamlit as st
import os
from pathlib import Path
import datetime

# 設定 GCP 認證
# 使用 gcloud 登入的憑證，不需要 credentials.json

# BigQuery 專案設定
PROJECT_ID = "data-model-final-project"
DATASET_FINAL = "netflix_final"  
DATASET_PREDICTIONS = "predictions"  
DATASET_MODELS = "models"


@st.cache_data(ttl=3600)  # 快取 1 小時
def get_top10_predictions(date_str: str = None, lookback_days: int = 0):
    """
    從 BigQuery 讀取最新的 Top 10 預測結果
    
    回傳:
        tuple: (DataFrame, snapshot_table_name) 若成功；失敗回傳 None
    """
    try:
        client = bigquery.Client(project=PROJECT_ID)
        # 預設會優先嘗試使用 dataset 中最新的 snapshot table：prediction_YYYYMMDD
        # 若找不到再回退到 prediction_latest。若使用者提供 date_str 或 lookback_days，則以該邏輯為主。
        table_to_query = f"{PROJECT_ID}.{DATASET_PREDICTIONS}.prediction_latest"

        # 如果使用者沒有指定 date_str 且沒有要求回溯，嘗試自動尋找 dataset 中最新的 prediction_YYYYMMDD
        if not date_str and lookback_days == 0:
            try:
                dataset_ref = f"{PROJECT_ID}.{DATASET_PREDICTIONS}"
                tables = list(client.list_tables(dataset_ref))
                latest_date = None
                latest_table = None
                for t in tables:
                    # t.table_id 可能是 like 'prediction_20251130' or 'prediction_latest'
                    tid = t.table_id
                    if tid.startswith('prediction_') and len(tid) >= len('prediction_') + 8:
                        suffix = tid.replace('prediction_', '')
                        # Expect suffix to be YYYYMMDD
                        try:
                            dt = datetime.datetime.strptime(suffix, '%Y%m%d')
                            if latest_date is None or dt > latest_date:
                                latest_date = dt
                                latest_table = f"{dataset_ref}.{tid}"
                        except Exception:
                            continue
                if latest_table:
                    table_to_query = latest_table
            except Exception:
                # 如果列表失敗（權限等），退回到後續的日期搜尋或 prediction_latest
                pass

        # 決定要檢查的日期列表（包含指定日期或今天，並視 lookback_days 向前搜尋）
        dates_to_try = []
        if date_str:
            try:
                base_date = datetime.datetime.strptime(date_str, "%Y%m%d")
            except Exception:
                # 如果傳入格式不正確，改用今天
                base_date = datetime.datetime.utcnow()
        else:
            base_date = datetime.datetime.utcnow()

        for d in range(0, max(lookback_days, 0) + 1):
            try_date = (base_date - datetime.timedelta(days=d)).strftime("%Y%m%d")
            dates_to_try.append(try_date)

        # 只有在使用者明確指定日期或 lookback 時，才優先採用日期回溯策略
        if date_str or lookback_days > 0:
            for try_date in dates_to_try:
                candidate = f"{PROJECT_ID}.{DATASET_PREDICTIONS}.prediction_{try_date}"
                try:
                    # 嘗試取得 table metadata
                    client.get_table(candidate)
                    table_to_query = candidate
                    break
                except Exception:
                    # table 不存在或無法存取，繼續下一個日期
                    continue

        # 建立查詢，從選定的 table 讀取並提取 label=1 的機率
        query = f"""
        WITH prob_extracted AS (
            SELECT
                uid,
                title,
                type,
                country,
                language,
                imdb_rating,
                tmdb_popularity,
                tmdb_vote_count,
                tmdb_vote_average,
                log_budget,
                log_revenue,
                release_year,
                duration_val,
                predicted_future_viral_14d,
                predicted_future_viral_14d_probs,
                -- 提取 label=1 (爆紅) 的機率
                (SELECT prob FROM UNNEST(predicted_future_viral_14d_probs) WHERE label = 1) as viral_prob
            FROM `{table_to_query}`
            WHERE predicted_future_viral_14d_probs IS NOT NULL
        )
        SELECT *
        FROM prob_extracted
        WHERE viral_prob IS NOT NULL
        ORDER BY viral_prob DESC
        LIMIT 10
        """

        df = client.query(query).to_dataframe()

        if not df.empty:
            # 轉換為百分比
            df['viral_probability'] = (df['viral_prob'] * 100).round(1)

            # 回傳 dataframe 與實際查詢所用的 table 名稱
            return df, table_to_query
        else:
            return None
        
    except Exception as e:
        st.error(f"❌ 讀取預測資料失敗：{str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

@st.cache_data(ttl=3600)
def get_all_titles():
    """
    取得所有可查詢的作品列表
    
    回傳:
        list: 作品名稱列表
    """
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # 從 final_dataset_ready 讀取
        query = f"""
        SELECT DISTINCT title
        FROM `{PROJECT_ID}.{DATASET_FINAL}.final_dataset_ready`
        WHERE title IS NOT NULL
        ORDER BY title
        """
        
        df = client.query(query).to_dataframe()
        return df['title'].tolist()
        
    except Exception as e:
        st.error(f"❌ 讀取作品列表失敗：{str(e)}")
        return []


@st.cache_data(ttl=3600)
def get_title_details(title):
    """
    查詢特定作品的詳細資訊
    
    參數:
        title: str, 作品名稱
    
    回傳:
        dict: 作品詳細資訊
    """
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # 從 final_dataset_ready 查詢
        query = f"""
        SELECT
            uid,
            title,
            type,
            country,
            language,
            release_year,
            rating as imdb_rating,
            genres,
            date_added,
            popularity as tmdb_popularity,
            vote_count as tmdb_vote_count,
            vote_average as tmdb_vote_average,
            budget,
            revenue,
            weeks_on_top10,
            best_rank,
            on_top10_total_views,
            on_top10_total_hours,
            views_2023,
            hours_2023,
            views_2024,
            hours_2024,
            views_2025,
            hours_2025,
            future_viral_14d
        FROM `{PROJECT_ID}.{DATASET_FINAL}.final_dataset_ready`
        WHERE title = @title
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("title", "STRING", title)
            ]
        )
        
        df = client.query(query, job_config=job_config).to_dataframe()
        
        if not df.empty:
            result = df.iloc[0].to_dict()
            return result
        else:
            return None
            
    except Exception as e:
        st.error(f"❌ 查詢失敗：{str(e)}")
        return None


@st.cache_data(ttl=3600)
def get_feature_importance():
    """
    取得 Feature Importance (根據 XGBoost 結果) !這是寫死的!
    
    回傳:
        DataFrame: feature 和 importance
    """
    # 根據你們 PPT 的圖表數據
    importance_data = {
        'feature': [
            'log_revenue', 'release_year', 'tmdb_vote_count', 'log_budget',
            'type', 'language', 'imdb_rating', 'tmdb_popularity',
            'primary_genre', 'country', 'duration_val', 'tmdb_vote_average'
        ],
        'importance': [
            3.6, 3.4, 3.2, 2.6, 2.2, 2.0, 1.9, 1.6, 1.5, 1.3, 0.2, 0.1
        ],
        'feature_zh': [
            '票房收益 (log)', '發行年份', 'TMDB 投票數', '製作預算 (log)',
            '作品類型', '語言', 'IMDb 評分', 'TMDB 熱度',
            '主要類別', '製作國家', '時長', 'TMDB 平均分'
        ]
    }
    
    df = pd.DataFrame(importance_data)
    df = df.sort_values('importance', ascending=False)
    
    return df


@st.cache_data(ttl=86400)  # 快取 24 小時
def get_model_performance():
    """
    取得模型效能指標（根據 PPT）!寫死的資料!
    
    回傳:
        dict: 模型效能資訊
    """
    return {
        'XGBoost': {
            'model_name': 'Gradient Boosted Tree',
            'roc_auc': 0.9565,
            'accuracy': 0.9729,
            'recall': 0.1724,
            'f1_score': 0.2702,
            'precision': 0.625
        },
        'Logistic_Regression': {
            'model_name': 'Baseline Logistic Regression',
            'roc_auc': 0.8399,
            'accuracy': 0.9729,
            'recall': 0.0230,
            'f1_score': 0.0397,
            'precision': 0.1429
        }
    }


def test_connection():
    """
    測試 BigQuery 連接
    
    回傳:
        bool: 連接是否成功
    """
    try:
        client = bigquery.Client(project=PROJECT_ID)
        query = "SELECT 1 as test"
        result = client.query(query).result()
        return True
    except Exception as e:
        st.error(f"❌ BigQuery 連接失敗：{str(e)}")
        return False


@st.cache_data(ttl=3600)
def get_title_viral_rate(title: str, date_str: str = None, lookback_days: int = 0):
    """
    取得特定作品的爆紅率（未來 14 天）
    從 prediction_YYYYMMDD 或 prediction_latest 讀取
    
    參數:
        title: str, 作品名稱
        date_str: str, 指定日期 (YYYYMMDD 格式)
        lookback_days: int, 向前搜尋天數
    
    回傳:
        float: 爆紅率百分比 (0-100)，若無資料回傳 None
    """
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # 決定要查詢的表，邏輯同 get_top10_predictions()
        table_to_query = f"{PROJECT_ID}.{DATASET_PREDICTIONS}.prediction_latest"

        # 如果使用者沒有指定 date_str 且沒有要求回溯，嘗試自動尋找 dataset 中最新的 prediction_YYYYMMDD
        if not date_str and lookback_days == 0:
            try:
                dataset_ref = f"{PROJECT_ID}.{DATASET_PREDICTIONS}"
                tables = list(client.list_tables(dataset_ref))
                latest_date = None
                latest_table = None
                for t in tables:
                    tid = t.table_id
                    if tid.startswith('prediction_') and len(tid) >= len('prediction_') + 8:
                        suffix = tid.replace('prediction_', '')
                        try:
                            dt = datetime.datetime.strptime(suffix, '%Y%m%d')
                            if latest_date is None or dt > latest_date:
                                latest_date = dt
                                latest_table = f"{dataset_ref}.{tid}"
                        except Exception:
                            continue
                if latest_table:
                    table_to_query = latest_table
            except Exception:
                pass

        # 決定要檢查的日期列表
        dates_to_try = []
        if date_str:
            try:
                base_date = datetime.datetime.strptime(date_str, "%Y%m%d")
            except Exception:
                base_date = datetime.datetime.utcnow()
        else:
            base_date = datetime.datetime.utcnow()

        for d in range(0, max(lookback_days, 0) + 1):
            try_date = (base_date - datetime.timedelta(days=d)).strftime("%Y%m%d")
            dates_to_try.append(try_date)

        # 只有在使用者明確指定日期或 lookback 時，才優先採用日期回溯策略
        if date_str or lookback_days > 0:
            for try_date in dates_to_try:
                candidate = f"{PROJECT_ID}.{DATASET_PREDICTIONS}.prediction_{try_date}"
                try:
                    client.get_table(candidate)
                    table_to_query = candidate
                    break
                except Exception:
                    continue

        # 查詢該作品的爆紅率
        query = f"""
        SELECT
            (SELECT prob FROM UNNEST(predicted_future_viral_14d_probs) WHERE label = 1) as viral_prob
        FROM `{table_to_query}`
        WHERE title = @title
        LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("title", "STRING", title)
            ]
        )

        df = client.query(query, job_config=job_config).to_dataframe()

        if not df.empty and 'viral_prob' in df.columns:
            viral_prob = df.iloc[0]['viral_prob']
            if viral_prob is not None:
                return float(viral_prob) * 100
        
        return None

    except Exception as e:
        # 靜默失敗，不顯示錯誤訊息
        return None