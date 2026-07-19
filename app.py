import streamlit as st
import json
from logic.scoring import calculate_phq9

# ==========================================
# 1. 数据读取层 (Model 接入)
# ==========================================
def load_scale_data(filepath="data/scales.json"):
    """读取解耦的 JSON 题库"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# 加载数据
scale_db = load_scale_data()
phq9_data = scale_db["PHQ-9"]

# ==========================================
# 2. 页面基础设置 (View 初始化)
# ==========================================
st.set_page_config(page_title=phq9_data["name"], page_icon="🧠", layout="centered")
st.title(phq9_data["name"])
st.write(phq9_data["description"])
st.divider() # 画一条分割线

# ==========================================
# 3. 状态管理 (Session State)
# ==========================================
# 如果记忆中没有 answers，就建一个初始全为 0 的列表，长度等于题目数量 (9)
if "answers" not in st.session_state:
    st.session_state["answers"] = [0] * len(phq9_data["questions"])

# ==========================================
# 4. 动态渲染答题界面 (View)
# ==========================================
# 使用 st.form 打包所有题目，防止用户每次点击都触发网页重载
with st.form("phq9_form"):
    
    # 提取选项的文字列表 ["完全不会", "好几天", "一半以上的天数", "几乎每天"]
    options_labels = [opt["label"] for opt in phq9_data["options"]]
    
    # 遍历 JSON 里的每一道题，动态画出单选题
    for i, q in enumerate(phq9_data["questions"]):
        st.markdown(f"**第 {i+1} 题：{q['text']}**")
        
        # 渲染单选题组件
        choice = st.radio(
            label=f"q_{i}", # 这是给机器看的隐藏唯一ID
            options=options_labels,
            index=0, 
            label_visibility="collapsed" # 隐藏掉自带的label，用我们上面加粗的 markdown
        )
        
        # 将用户选择的文字选项，转换回对应的分数(0, 1, 2, 3)，存入状态记忆
        for opt in phq9_data["options"]:
            if opt["label"] == choice:
                st.session_state["answers"][i] = opt["score"]
                break
                
        st.write("") # 增加一点垂直留白，排版更美观

    # 表单提交按钮
    submitted = st.form_submit_button("提交问卷并生成报告", type="primary")

# ==========================================
# 5. 连接计分引擎调度层 (Controller)
# ==========================================
if submitted:
    try:
        # 将记忆里的分数列表，直接喂给我们在 logic 文件夹写的纯函数
        result = calculate_phq9(st.session_state["answers"])
        
        # 展示成果
        st.success("✅ 问卷提交成功！")
        st.metric(label="您的总得分", value=result["total_score"])
        
        # 根据严重程度给出不同颜色的视觉反馈
        severity = result["severity"]
        if "重度" in severity:
            st.error(f"临床建议：{severity}。请务必寻求专业心理医生的帮助。")
        elif "中度" in severity:
            st.warning(f"临床建议：{severity}。建议进行心理干预。")
        else:
            st.info(f"临床建议：{severity}。请继续保持良好的生活状态。")
            
    except Exception as e:
        # 触发质量门禁，拦截错误不让网页崩溃
        st.error(f"系统错误：{str(e)}")