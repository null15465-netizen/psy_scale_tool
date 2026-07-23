import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import List
from supabase import create_client, Client

# 读取安全密钥
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def init_db() -> None:
    pass

def save_record(answers: List[int], total_score: int, severity: str, user_id: str, scale_name: str) -> None:
    """
    将用户的答题记录动态路由写入到对应的 Supabase 云端数据库表中。
    :param scale_name: 当前量表的标识名（"PHQ-9", "GAD-7", "SCL-90"）
    """
    tz_beijing = timezone(timedelta(hours=8))
    current_time = datetime.now(tz_beijing).strftime("%Y-%m-%d %H:%M:%S")
    
    # 构造标准数据字典
    data = {
        "submit_time": current_time,
        "raw_answers": answers,
        "total_score": total_score,
        "severity": severity,
        "user_id": user_id
    }
    
    # 动态路由选择对应的数据库表名
    table_map = {
        "PHQ-9": "phq9_records",
        "GAD-7": "gad7_records",
        "SCL-90": "scl90_records"
    }
    target_table = table_map.get(scale_name, "phq9_records")
    
    # 执行云端安全插入
    supabase.table(target_table).insert(data).execute()