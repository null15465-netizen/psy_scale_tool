import streamlit as st
import json
import math
from logic.scoring import calculate_phq9
from logic.database import init_db, save_record

# ==========================================
# 1. 基础配置与 CSS 挂载
# ==========================================
st.set_page_config(page_title="临床量表评估平台", layout="centered")

def local_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
local_css("assets/custom.css")

# ==========================================
# 2. 状态初始化 (必须在所有 UI 渲染和数据加载之前执行)
# ==========================================
# 核心防线：在文件最顶部初始化所有 session_state 变量，确保后续读取绝不报错
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 0
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "error_msg" not in st.session_state:
    st.session_state["error_msg"] = ""
if "answers" not in st.session_state:
    # 临时初始化为空列表，读取数据后会根据题目长度重新校准
    st.session_state["answers"] = []

# ==========================================
# 3. 数据加载与数据库初始化
# ==========================================
@st.cache_data
def load_scale_data(filepath="data/scales.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

scale_db = load_scale_data()
phq9_data = scale_db["PHQ-9"]
init_db()

# 根据真实题库长度，校准内存中的答案列表
if len(st.session_state["answers"]) != len(phq9_data["questions"]):
    st.session_state["answers"] = [None] * len(phq9_data["questions"])

QUESTIONS_PER_PAGE = 3
total_questions = len(phq9_data["questions"])
total_pages = math.ceil(total_questions / QUESTIONS_PER_PAGE)

# 逻辑校验引擎
def validate_current_page(start_idx, end_idx):
    for i in range(start_idx, end_idx):
        if st.session_state["answers"][i] is None:
            return False, i + 1
    return True, -1

# ==========================================
# 4. 路由与界面渲染
# ==========================================
if not st.session_state["submitted"]:
    
    # 大标题 (强制不换行)
    st.markdown(f"<h1 class='main-title'>{phq9_data['name']}</h1>", unsafe_allow_html=True)
    
    # 指导语卡片
    st.markdown("""
    <div class="instruction-card">
        <p><strong>免费声明：</strong> 本测试完全免费，无需支付任何费用。</p>
        <p><strong>数据用途：</strong> 您的数据仅用于心理学科研统计分析，已开启匿名哈希加密，绝不外泄。</p>
        <p><strong>测试说明：</strong> 本量表共 9 道题，预计耗时 2-3 分钟。这是世界卫生组织推荐的抑郁筛查工具。</p>
        <p style="margin-bottom: 0;"><strong>测试目的：</strong> 在过去的两周里，您生活中以下症状出现的频率有多少？</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 输入框 (此时 user_id 已在最顶部完成初始化，绝对安全)
    st.session_state["user_id"] = st.text_input(
        "请输入您的被试编号或昵称（如 P01，以便记录）：", 
        value=st.session_state["user_id"]
    )
    
    # 唯一保留的进度条
    progress_val = (st.session_state["current_page"] + 1) / total_pages
    st.progress(progress_val, text=f"第 {st.session_state['current_page'] + 1} 部分 / 共 {total_pages} 部分")
    
    # 分割线
    st.markdown("<hr class='clinical-divider'>", unsafe_allow_html=True)
    
    # 错误提示拦截
    if st.session_state["error_msg"]:
        st.error(st.session_state["error_msg"])

    start_idx = st.session_state["current_page"] * QUESTIONS_PER_PAGE
    end_idx = min(start_idx + QUESTIONS_PER_PAGE, total_questions)
    current_questions = phq9_data["questions"][start_idx:end_idx]
    options_labels = [opt["label"] for opt in phq9_data["options"]]

    # 题目渲染
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
            horizontal=True
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
                # 校验 1：代号不能为空
                if not st.session_state["user_id"].strip():
                    st.session_state["error_msg"] = "⚠️ 请注意：必须先在顶部输入您的被试编号或昵称，才能进入下一部分。"
                    st.rerun()
                
                # 校验 2：当前页题目必填
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
                # 校验 1：代号不能为空
                if not st.session_state["user_id"].strip():
                    st.session_state["error_msg"] = "⚠️ 请注意：必须先在顶部输入您的被试编号或昵称，才能提交问卷。"
                    st.rerun()
                
                # 校验 2：当前页题目必填
                is_valid, err_q_num = validate_current_page(start_idx, end_idx)
                if is_valid:
                    st.session_state["error_msg"] = ""
                    st.session_state["submitted"] = True
                    st.rerun()
                else:
                    st.session_state["error_msg"] = f"请注意：第 {err_q_num} 题尚未作答，请完成后再提交。"
                    st.rerun()

else:
    # --- 结果页面 ---
    st.markdown("<h1 class='main-title'>评估报告</h1>", unsafe_allow_html=True)
    try:
        result = calculate_phq9(st.session_state["answers"])
        save_record(
            st.session_state["answers"], 
            result["total_score"], 
            result["severity"],
            st.session_state["user_id"]
        )
        
        st.success("问卷数据收集完成，您的数据已进入加密安全舱。")
        st.metric(label="PHQ-9 评估总分", value=result["total_score"])
        
        severity = result["severity"]
        st.markdown(f"### 诊断参考：<span style='color:#3f6653;'>{severity}</span>", unsafe_allow_html=True)
        
        if "重度" in severity:
            st.error("**详细说明：** 您的得分反映出强烈的抑郁症状。\n\n**应对建议：** 请您务必尽快前往专业的三甲医院精神心理科就诊，寻求药物干预与专业的心理咨询。不要独自承担，我们始终与您同在。")
        elif "中度" in severity:
            st.warning("**详细说明：** 您的得分反映出中等程度的抑郁倾向。\n\n**应对建议：** 建议您安排一次专业的心理咨询（如认知行为疗法 CBT）来梳理当前的情绪压力。平时可尝试增加户外运动和规律作息。若症状持续恶化，请及时就医。")
        else:
            st.info("**详细说明：** 您的得分在正常范围内。\n\n**应对建议：** 请继续保持现有的生活节奏，适度放松，享受生活。")
            
        if st.button("重新测试"):
            st.session_state.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"系统错误：{str(e)}")