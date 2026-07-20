import streamlit as st
import json
import math
from logic.scoring import calculate_phq9
from logic.database import init_db, save_record

# ==========================================
# 1. 数据加载与底层初始化
# ==========================================
def load_scale_data(filepath="data/scales.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

scale_db = load_scale_data()
phq9_data = scale_db["PHQ-9"]
init_db()

# ==========================================
# 2. UX: 页面观感设置 (整洁、好看)
# ==========================================
st.set_page_config(page_title=phq9_data["name"], page_icon="🌿", layout="centered")

# ==========================================
# 3. 高级状态管理 (支持分页、记忆与提交拦截)
# ==========================================
# 记忆 1: 答案列表 (用 -1 代表还未作答)
if "answers" not in st.session_state:
    st.session_state["answers"] = [-1] * len(phq9_data["questions"])
# 记忆 2: 当前停留在第几页
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 0
# 记忆 3: 是否已经交卷
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

# UX 策略：认知减负，每页只显示 3 道题
QUESTIONS_PER_PAGE = 3
total_questions = len(phq9_data["questions"])
# 计算总页数 (向上取整)
total_pages = math.ceil(total_questions / QUESTIONS_PER_PAGE)

# ==========================================
# 4. 界面路由：交卷前 vs 交卷后
# ==========================================
if not st.session_state["submitted"]:
    
    # --- 答题进行中界面 ---
    st.title(phq9_data["name"])
    
    # UX 洞察 1：明确指导语，消除虚无感
    st.info(f"**测试目的：** {phq9_data['description']}\n\n**隐私承诺：** 您的数据仅用于评估，将被严格加密。请完全凭借您的第一直觉进行滑动作答。")
    
    # UX 洞察 2：进度条反馈
    progress_val = (st.session_state["current_page"] + 1) / total_pages
    st.progress(progress_val, text=f"当前进度: 第 {st.session_state['current_page'] + 1} 部分 / 共 {total_pages} 部分")
    st.divider()

    # 计算当前页应该显示的题目范围 (例如第 0 页显示 0-2 题)
    start_idx = st.session_state["current_page"] * QUESTIONS_PER_PAGE
    end_idx = min(start_idx + QUESTIONS_PER_PAGE, total_questions)
    current_questions = phq9_data["questions"][start_idx:end_idx]
    
    options_labels = [opt["label"] for opt in phq9_data["options"]]

    # 渲染当前页的题目
    with st.form("quiz_form"):
        for i, q in enumerate(current_questions):
            # 获取这道题在总题库里的真实序号
            actual_q_index = start_idx + i 
            st.markdown(f"**{actual_q_index + 1}. {q['text']}**")
            
            # 读取历史答案：如果没答过就是 -1，那就默认指向最左边的选项 (0)
            current_ans_val = st.session_state["answers"][actual_q_index]
            default_index = 0 if current_ans_val == -1 else current_ans_val
            
            # UX 洞察 3：使用滑轨 (select_slider) 替代干瘪的单选框，增强“连续谱”的具象感
            choice = st.select_slider(
                label=f"q_{actual_q_index}",
                options=options_labels,
                value=options_labels[default_index],
                label_visibility="collapsed"
            )
            
            # 将滑轨选中的文字，转换成分数存入记忆
            for opt in phq9_data["options"]:
                if opt["label"] == choice:
                    st.session_state["answers"][actual_q_index] = opt["score"]
                    break
                    
            st.write("") # 增加垂直留白，视觉更清爽

        # UX 洞察 4：分页导航按钮
        cols = st.columns(3)
        with cols[0]:
            # 如果不是第一页，就显示“上一页”按钮
            if st.session_state["current_page"] > 0:
                if st.form_submit_button("⬅️ 上一部分"):
                    st.session_state["current_page"] -= 1
                    st.rerun()
                    
        with cols[2]:
            # 如果不是最后一页，显示“下一页”；否则显示“提交”
            if st.session_state["current_page"] < total_pages - 1:
                if st.form_submit_button("下一部分 ➡️", type="primary"):
                    st.session_state["current_page"] += 1
                    st.rerun()
            else:
                if st.form_submit_button("✅ 提交最终问卷", type="primary"):
                    st.session_state["submitted"] = True
                    st.rerun()

else:
    # --- 交卷后的结果界面 ---
    st.title("测试完成")
    try:
        # 调用核心算法与数据库，执行底层操作
        result = calculate_phq9(st.session_state["answers"])
        save_record(st.session_state["answers"], result["total_score"], result["severity"])
        
        # 结果展示
        st.success("✅ 数据已安全加密保存！感谢您的耐心作答与信任。")
        st.metric(label="您的总得分", value=result["total_score"])
        
        severity = result["severity"]
        if "重度" in severity:
            st.error(f"**临床参考：** {severity}。请务必寻求专业心理医生的帮助。")
        elif "中度" in severity:
            st.warning(f"**临床参考：** {severity}。建议进行心理干预或密切关注情绪变化。")
        else:
            st.info(f"**临床参考：** {severity}。请继续保持良好的生活状态。")
            
        # 提供重新测试的入口
        if st.button("重新测试"):
            st.session_state.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"系统错误：{str(e)}")