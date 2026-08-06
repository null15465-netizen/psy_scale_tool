import streamlit as st
import streamlit.components.v1 as components
import json
import math
import importlib
from datetime import datetime, timezone, timedelta
from logic.database import init_db, save_record

# ==========================================
# 1. 基础配置与 CSS 挂载
# ==========================================
st.set_page_config(page_title="临床量表评估平台", layout="centered")

def local_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
local_css("assets/custom.css")

# 每次翻页后自动回到页面顶部
components.html(
    "<script>window.parent.scrollTo({top: 0, behavior: 'instant'});</script>",
    height=0
)

# 核心清洗工具
def clean_html(html_str: str) -> str:
    return "".join([line.strip() for line in html_str.split("\n")])

# ==========================================
# 2. 状态初始化
# ==========================================
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 0
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "error_msg" not in st.session_state:
    st.session_state["error_msg"] = ""
if "answers" not in st.session_state:
    st.session_state["answers"] = []

# ==========================================
# 3. 数据加载与 URL 路由解析 (Router)
# ==========================================
@st.cache_data
def load_scale_data(filepath="data/scales.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

scale_db = load_scale_data()
init_db()

# 核心改动：解析浏览器地址栏参数（例如 ?scale=scl-90）
query_params = st.query_params
query_scale = query_params.get("scale", "").upper().strip()

# 自动匹配对应量表的默认索引
scale_keys = list(scale_db.keys())
default_index = 0

if query_scale in scale_keys:
    default_index = scale_keys.index(query_scale)
elif query_scale.replace("-", "") in [k.lower().replace("-", "") for k in scale_keys]:
    # 兼容中划线，如 scl90 或 scl-90 均能匹配到 SCL-90
    for idx, k in enumerate(scale_keys):
        if k.lower().replace("-", "") == query_scale.replace("-", ""):
            default_index = idx
            break

# 侧边栏量表选择
st.sidebar.markdown("## 量表选择")
selected_scale = st.sidebar.selectbox(
    "请选择您要进行的评估：",
    options=scale_keys,
    index=default_index # 使用解析出的默认索引，实现直达
)

# 路由守护：当切换量表时清空状态
if "current_scale" not in st.session_state:
    st.session_state["current_scale"] = selected_scale

if st.session_state["current_scale"] != selected_scale:
    st.session_state.clear()
    st.session_state["current_scale"] = selected_scale
    st.rerun()

current_scale_data = scale_db[selected_scale]

# ==========================================
# 4. 动态载入对应算法模块
# ==========================================
module_name = selected_scale.lower().replace("-", "")
try:
    scale_module = importlib.import_module(f"logic.scales.{module_name}")
except ModuleNotFoundError:
    st.error(f"系统错误：未找到量表 {selected_scale} 的计算模块 logic.scales.{module_name}")
    st.stop()

# 根据题库长度重设答案列表
if len(st.session_state["answers"]) != len(current_scale_data["questions"]):
    st.session_state["answers"] = [None] * len(current_scale_data["questions"])

# 动态设定分页大小
if selected_scale == "SCL-90":
    QUESTIONS_PER_PAGE = 10
elif selected_scale in ["SDS", "SAS"]:
    QUESTIONS_PER_PAGE = 5
elif selected_scale == "PSS":
    QUESTIONS_PER_PAGE = 5
else:
    QUESTIONS_PER_PAGE = 3

total_questions = len(current_scale_data["questions"])
total_pages = math.ceil(total_questions / QUESTIONS_PER_PAGE)

def validate_current_page(start_idx, end_idx):
    if current_scale_data.get("allow_skip"):
        return True, -1
    for i in range(start_idx, end_idx):
        if st.session_state["answers"][i] is None:
            return False, i + 1
    return True, -1

# ==========================================
# 5. 前端界面渲染
# ==========================================
if not st.session_state["submitted"]:
    
    st.markdown(f"<h1 class='main-title'>{current_scale_data['name']}</h1>", unsafe_allow_html=True)
    
    if "instruction" in current_scale_data:
        st.markdown(f"<div class='instruction-card'>{clean_html(current_scale_data['instruction'])}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="instruction-card">
            <p><strong>免费声明：</strong> 本测试免费，无需支付费用。</p>
            <p><strong>数据用途：</strong> 数据仅用于心理学科研统计分析，测试结果严格保密。</p>
            <p><strong>测试说明：</strong> 本量表共 {total_questions} 道题，预计耗时 {current_scale_data.get("duration", "10-15" if selected_scale == "SCL-90" else "2-3")} 分钟。</p>
            <p style="margin-bottom: 0;"><strong>测试目的：</strong> {current_scale_data['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.session_state["user_id"] = st.text_input(
        "请输入您的被试编号或昵称（如 P01，以便记录）：", 
        value=st.session_state["user_id"]
    )
    
    progress_val = (st.session_state["current_page"] + 1) / total_pages
    st.progress(progress_val, text=f"第 {st.session_state['current_page'] + 1} 部分 / 共 {total_pages} 部分")
    st.markdown("<hr class='clinical-divider'>", unsafe_allow_html=True)
    
    if st.session_state["error_msg"]:
        st.error(st.session_state["error_msg"])

    start_idx = st.session_state["current_page"] * QUESTIONS_PER_PAGE
    end_idx = min(start_idx + QUESTIONS_PER_PAGE, total_questions)
    current_questions = current_scale_data["questions"][start_idx:end_idx]

    for i, q in enumerate(current_questions):
        actual_q_index = start_idx + i 
        
        q_options = q.get("options") or current_scale_data["options"]
        q_labels = [opt["label"] for opt in q_options]

        if q.get("free_text"):
            current_text = st.session_state["answers"][actual_q_index] or ""
            txt = st.text_input(
                label=f"{actual_q_index + 1}. {q['text']}",
                value=current_text,
                key=f"text_{actual_q_index}"
            )
            st.session_state["answers"][actual_q_index] = txt.strip()
            continue

        current_ans_val = st.session_state["answers"][actual_q_index]
        default_index = None
        if current_ans_val is not None:
            for opt_idx, opt in enumerate(q_options):
                if opt["score"] == current_ans_val:
                    default_index = opt_idx
                    break
        
        choice = st.radio(
            label=f"{actual_q_index + 1}. {q['text']}",
            options=q_labels,
            index=default_index,
            key=f"radio_{actual_q_index}",
            horizontal=len(q_options) <= 8
        )
        
        if choice is not None:
            for opt in q_options:
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
                if not st.session_state["user_id"].strip():
                    st.session_state["error_msg"] = "请注意：必须先在顶部输入您的被试编号或昵称，才能进入下一部分。"
                    st.rerun()
                
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
                if not st.session_state["user_id"].strip():
                    st.session_state["error_msg"] = "请注意：必须先在顶部输入您的被试编号或昵称，才能提交问卷。"
                    st.rerun()
                
                is_valid, err_q_num = validate_current_page(start_idx, end_idx)
                if is_valid:
                    st.session_state["error_msg"] = ""
                    st.session_state["submitted"] = True
                    st.rerun()
                else:
                    st.session_state["error_msg"] = f"请注意：第 {err_q_num} 题尚未作答，请完成后再提交。"
                    st.rerun()

else:
    # ==========================================
    # 6. 结果报告生成与导出 (由模块完全自决)
    # ==========================================
    st.markdown("<h1 class='main-title'>评估报告</h1>", unsafe_allow_html=True)
    try:
        tz_beijing = timezone(timedelta(hours=8))
        current_time = datetime.now(tz_beijing).strftime("%Y-%m-%d %H:%M:%S")

        result = scale_module.calculate(st.session_state["answers"])
        
        save_record(
            st.session_state["answers"], 
            result["total_score"], 
            f"{selected_scale}: {result['severity']}", 
            st.session_state["user_id"],
            selected_scale
        )
        
        st.markdown(clean_html(result["html_report"]), unsafe_allow_html=True)

        st.markdown("<hr class='clinical-divider'>", unsafe_allow_html=True)
        st.markdown("### 💾 报告与数据导出")
        
        with open("assets/custom.css", "r", encoding="utf-8") as f:
            embedded_css = f.read()
        
        html_report_content = f"""<!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>{current_scale_data['name']} - 离线临床报告</title>
            <style>
                {embedded_css}
                @media print {{
                    body {{ background-color: #ffffff !important; padding: 20px !important; color: #1c201d !important; }}
                    .block-container {{ max-width: 100% !important; }}
                    .instruction-card {{ box-shadow: none !important; background-color: #ffffff !important; border-color: #cccccc !important; }}
                    .main-title, .instruction-card *, .clinical-report-container *, .report-section, .clinical-table, .clinical-table * {{ color: #1c201d !important; }}
                    .report-section {{ background-color: #ffffff !important; border-color: #cccccc !important; box-shadow: none !important; }}
                    .clinical-table th {{ background-color: #f0f0ec !important; }}
                    .highlight-red {{ color: #ba1a1a !important; }}
                    .highlight-green {{ color: #3f6653 !important; }}
                }}
            </style>
        </head>
        <body class="bg-surface-dim antialiased" style="background-color: #0a0e0c; padding: 40px 20px;">
            <div class="block-container" style="max-width: 800px; margin: 0 auto;">
                <h1 class="main-title" style="text-align: center; color: #f1ede1; font-size: 2.2rem; font-weight: bold; margin-bottom: 30px;">
                    {current_scale_data['name']} 评估报告
                </h1>
                <div class="instruction-card" style="background-color:#151a17; padding:30px; border-radius:14px; border: 1px solid rgba(241,237,225,0.14); margin-bottom: 30px; box-shadow: 0 6px 24px rgba(0,0,0,0.35);">
                    <p style="margin-bottom: 15px; font-size:1.05rem;"><strong>被试代号：</strong>{st.session_state['user_id']}</p>
                    <p style="margin-bottom: 15px; font-size:1.05rem;"><strong>评估时间：</strong>{current_time}</p>
                    <p style="margin-bottom: 0; font-size:1.05rem;"><strong>安全声明：</strong>本报告基于专业心理学量表计算得出，数据保密。本报告仅供科研与自我认知参考，不替代临床医学诊断。</p>
                </div>
                {result["html_report"]}
            </div>
        </body>
        </html>
        """
        
        # 组装自适应 CSV 数据
        csv_content = result.get("csv_header", f"评估量表,{selected_scale}\n")
        csv_content += f"被试代号,{st.session_state['user_id']}\n评估时间,{current_time}\n"
        csv_content += result.get("csv_rows", f"总分,{result['total_score']},{result['severity']},-\n")

        exp_cols = st.columns(2)
        with exp_cols[0]:
            st.download_button(
                label="导出 HTML 离线报告 (可打印PDF)",
                data=html_report_content,
                file_name=f"{module_name}_Report_{st.session_state['user_id']}.html",
                mime="text/html",
                use_container_width=True
            )
        with exp_cols[1]:
            st.download_button(
                label="导出 Excel (CSV) 原始数据",
                data=csv_content.encode("utf-8-sig"),
                file_name=f"{module_name}_Data_{st.session_state['user_id']}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.write("")
        if st.button("重新测试", key=f"reset_{module_name}"):
            st.session_state.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"系统错误：{str(e)}")
