import sqlite3
import json
from datetime import datetime
from typing import List

# 定义数据库文件的物理存放位置（生成在根目录下）
DB_PATH = "psy_records.db"

def init_db() -> None:
    """
    初始化数据库：如果表不存在，则自动创建。
    """
    # 建立连接
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 执行 SQL 语句：创建名为 phq9_records 的表
    # 包含字段：自增ID, 提交时间, 原始答案(存为JSON字符串), 总分, 严重程度
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS phq9_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submit_time TEXT NOT NULL,
            raw_answers TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            severity TEXT NOT NULL
        )
    ''')
    
    # 提交修改并关闭连接
    conn.commit()
    conn.close()

def save_record(answers: List[int], total_score: int, severity: str) -> None:
    """
    纯副作用函数：将一条答题记录安全插入到数据库中。
    :param answers: 用户的原始分数列表
    :param total_score: 计算出的总分
    :param severity: 临床诊断结果
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    answers_json = json.dumps(answers) # 将 Python 列表转成 JSON 字符串才能存入数据库文本字段
    
    # 质量门禁：使用 ? 占位符而不是 f-string 直接拼接，这是防止 SQL 注入攻击的行业铁律
    cursor.execute('''
        INSERT INTO phq9_records (submit_time, raw_answers, total_score, severity)
        VALUES (?, ?, ?, ?)
    ''', (current_time, answers_json, total_score, severity))
    
    conn.commit()
    conn.close()