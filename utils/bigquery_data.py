"""
BigQuery 資料讀取功能 - Netflix 爆紅預測系統
"""
from google.cloud import bigquery
import pandas as pd
import streamlit as st
import os
from pathlib import Path

# 設定 GCP 認證
# 使用 gcloud 登入的憑證，不需要 credentials.json

# BigQuery 專案設定
PROJECT_ID = "data-model-final-project"
DATASET_FINAL = "netflix_final"  
DATASET_PREDICTIONS = "predictions"  
DATASET_MODELS = "models"


@st.cache_data(ttl=3600)  # 快取 1 小時
def get_top10_predictions():
    """
    從 BigQuery 讀取最新的 Top 10 預測結果
    
    回傳:
        DataFrame: 包含 title, type, country, viral_probability 等欄位
    """
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # 從 predictions.prediction_latest 讀取
        # 提取 label=1 (會爆紅) 的機率並排序
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
            FROM `{PROJECT_ID}.{DATASET_PREDICTIONS}.prediction_latest`
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

            return df
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