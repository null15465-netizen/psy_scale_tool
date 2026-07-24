import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import List
from supabase import create_client, Client

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def init_db() -> None:
    pass

def save_record(answers: List[int], total_score: int, severity: str, user_id: str, scale_name: str) -> None:
    """
    将用户的答题记录动态路由写入到对应的 Supabase 云端数据库表中。
    """
    tz_beijing = timezone(timedelta(hours=8))
    current_time = datetime.now(tz_beijing).strftime("%Y-%m-%d %H:%M:%S")
    
    data = {
        "submit_time": current_time,
        "raw_answers": answers,
        "total_score": total_score,
        "severity": severity,
        "user_id": user_id
    }
    
    # 动态路由表名（增加 SDS 和 SAS）
    table_map = {
        "PHQ-9": "phq9_records",
        "GAD-7": "gad7_records",
        "SCL-90": "scl90_records",
        "SDS": "sds_records",
        "SAS": "sas_records"
    }
    target_table = table_map.get(scale_name, "phq9_records")
    
    supabase.table(target_table).insert(data).execute()