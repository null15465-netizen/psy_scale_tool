import streamlit as st
from supabase import create_client, Client
import json
from datetime import datetime
from typing import List

# ==========================================
# 1. 初始化云端数据库连接
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    """利用 Streamlit 的密码箱安全读取配置，并建立长连接"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# 获取全局数据库客户端实例
supabase = init_connection()

def init_db() -> None:
    """
    云端 PostgreSQL 不需要代码自动建表，表结构已在 Supabase 后台手动创建。
    这里保留空函数，防止 app.py 报错。
    """
    pass

# ==========================================
# 2. 插入数据记录
# ==========================================
def save_record(answers: List[int], total_score: int, severity: str, user_id: str) -> None:
    """将患者数据通过 API 推送至 Supabase 云端"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    answers_json = json.dumps(answers)
    
    # 执行插入操作，对应刚才在云端创建的 phq9_records 表
    data, count = supabase.table('phq9_records').insert({
        "submit_time": current_time,
        "raw_answers": answers_json,
        "total_score": total_score,
        "severity": severity,
        "user_id": user_id
    }).execute()