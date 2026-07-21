import streamlit as st
import json
import math
from logic.scoring import calculate_phq9
from logic.database import init_db, save_record

st.set_page_config(page_title="临床量表评估平台", layout="centered")

def local_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
local_css("assets/custom.css")

@st.cache_data
def load_scale_data(filepath="data/scales.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

scale_db = load_scale_data()
phq9_data = scale_db["PHQ-9"]
init_db()

if "answers" not in st.session_state:
    st.session_state["answers"] = [None] * len(phq9_data["questions"])
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 0
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "error_msg" not in st.session_state:
    st.session_state["error_msg"] = ""

QUESTIONS_PER_PAGE = 3
total_questions = len(phq9_data["questions"])
total_pages = math.ceil(total_questions / QUESTIONS_PER_PAGE)

def validate_current_page(start_idx, end_idx):
    for i in range(start_idx, end_idx):
        if st.session_state["answers"][i] is None:
            return False, i + 1
    return True, -1

if not st.session_state["submitted"]:
    
    st.markdown(f"<h1 style='text-align: center; color: #012d1d; margin-bottom: 30px; white-space: nowrap;'>{phq9_data['name']}</h1>", unsafe_allow_html=True)
    
    # 采用统一的 class="instruction-card" 与题目卡片等宽对齐
    st.markdown("""
    <div class="instruction-card">
        <p style="font-size: 1.1rem; line-height: 1.8; margin-bottom: 12px;"><strong style="color:#012d1d;">免费声明：</strong> 本测试完全免费，无需支付任何费用。</p>
        <p style="font-size: 1.1rem; line-height: 1.8; margin-bottom: 12px;"><strong style="color:#012d1d;">数据用途：</strong> 您的数据仅用于心理学科研统计分析，个人信息将得到保护。</p>
        <p style="font-size: 1.1rem; line-height: 1.8; margin-bottom: 12px;"><strong style="color:#012d1d;">测试说明：</strong> 本量表共 9 道题，预计耗时 2-3 分钟。这是世界卫生组织推荐的抑郁筛查工具。</p>
        <p style="font-size: 1.1rem; line-height: 1.8; margin-bottom: 0;"><strong style="color:#012d1d;">请您回答：</strong> 在过去的两周里，您生活中以下症状出现的频率有多少？</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 保留唯一一个进度条
    progress_val = (st.session_state["current_page"] + 1) / total_pages
    st.progress(progress_val, text=f"第 {st.session_state['current_page'] + 1} 部分 / 共 {total_pages} 部分")
    
    if st.session_state["error_msg"]:
        st.error(st.session_state["error_msg"])

    start_idx = st.session_state["current_page"] * QUESTIONS_PER_PAGE
    end_idx = min(start_idx + QUESTIONS_PER_PAGE, total_questions)
    current_questions = phq9_data["questions"][start_idx:end_idx]
    options_labels = [opt["label"] for opt in phq9_data["options"]]

    for i, q in enumerate(current_questions):
        actual_q_index = start_idx + i 
        
        current_ans_val = st.session_state["answers"][actual_q_index]
        default_index = None
        if current_ans_val is not None:
            for opt_idx, opt in enumerate(phq9_data["options"]):
                if opt["score"] == current_ans_val:
                    default_index = opt_idx
                    break
        
        choice = st.radio(
            label=f"{actual_q_index + 1}. {q['text']}",
            options=options_labels,
            index=default_index,
            key=f"radio_{actual_q_index}",
            horizontal=True  # <-- 增加这极其关键的一行，打通底层横向排版
        )
        
        if choice is not None:
            for opt in phq9_data["options"]:
                if opt["label"] == choice:
                    st.session_state["answers"][actual_q_index] = opt["score"]
                    break

    st.write("")
    cols = st.columns(3)
    
    with cols[0]:
        if st.session_state["current_page"] > 0:
            if st.button("上一部分"):
                st.session_state["error_msg"] = "" 
                st.session_state["current_page"] -= 1
                st.rerun()
                
    with cols[2]:
        if st.session_state["current_page"] < total_pages - 1:
            if st.button("下一部分", type="primary"):
                is_valid, err_q_num = validate_current_page(start_idx, end_idx)
                if is_valid:
                    st.session_state["error_msg"] = ""
                    st.session_state["current_page"] += 1
                    st.rerun()
                else:
                    st.session_state["error_msg"] = f"请注意：第 {err_q_num} 题尚未作答，请完成后再进入下一部分。"
                    st.rerun()
        else:
            if st.button("提交最终问卷", type="primary"):
                is_valid, err_q_num = validate_current_page(start_idx, end_idx)
                if is_valid:
                    st.session_state["error_msg"] = ""
                    st.session_state["submitted"] = True
                    st.rerun()
                else:
                    st.session_state["error_msg"] = f"请注意：第 {err_q_num} 题尚未作答，请完成后再提交。"
                    st.rerun()

else:
    st.markdown("<h1 style='text-align: center;'>评估报告</h1>", unsafe_allow_html=True)
    try:
        result = calculate_phq9(st.session_state["answers"])
        save_record(st.session_state["answers"], result["total_score"], result["severity"])
        
        st.success("问卷数据收集完成，感谢您的配合！")
        st.metric(label="PHQ-9 评估总分", value=result["total_score"])
        
        severity = result["severity"]
        st.markdown(f"### 诊断参考：<span style='color:#3f6653;'>{severity}</span>", unsafe_allow_html=True)
        
        if "重度" in severity:
            st.error("详细说明：您的得分反映出强烈的抑郁症状，建议尽快寻求专业帮助")
        elif "中度" in severity:
            st.warning("详细说明：您的得分反映出中等程度的抑郁倾向，建议寻求专业帮助")
        else:
            st.info("详细说明：您的得分在正常范围内，但建议持续关注心理健康")
            
        if st.button("重新测试"):
            st.session_state.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"系统错误：{str(e)}")