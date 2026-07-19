import streamlit as st
import csv
from datetime import datetime

# 这是网站的标题
st.title("我的首个心理测量工具调试工程")

# 这是一段简单的文本说明
st.write("欢迎来到这里，这是一个用来测试 AI 辅助开发的问卷工具。")

# 这是一个文本输入框，用于输入被试编号
participant_id = st.text_input("请输入被试编号（如 P001）：")

# 这是一个单选题
mood = st.radio("你今天的心情怎么样？", ["非常好", "一般", "有点低落"])

# 这是一个提交按钮
if st.button("提交回答"):
    # 1. 获取当前系统时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. 打开（或自动创建）一个名为 results.csv 的文件
    # mode="a" 表示“追加 (append)”，不会覆盖之前的数据
    # encoding="utf-8-sig" 是为了防止表格在 Windows 的 Excel 里打开时中文乱码
    with open("results.csv", mode="a", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        # 3. 写入一行数据：[提交时间, 被试编号, 选择的心情]
        writer.writerow([current_time, participant_id, mood])
        
    # 4. 在网页上给出成功提示
    st.success(f"收到！你的心情 '{mood}' 已成功保存至后台数据库！")