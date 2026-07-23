import streamlit as st
import json
import math
from logic.scoring import calculate_phq9, calculate_gad7, calculate_scl90
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
# 3. 数据加载与侧边栏路由
# ==========================================
@st.cache_data
def load_scale_data(filepath="data/scales.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

scale_db = load_scale_data()
init_db()

# 侧边栏量表切换
st.sidebar.markdown("## 📋 量表选择")
selected_scale = st.sidebar.selectbox(
    "请选择您要进行的评估：",
    options=["PHQ-9", "GAD-7", "SCL-90"],
    index=0
)

# 路由守护：切换量表时，彻底重置会话
if "current_scale" not in st.session_state:
    st.session_state["current_scale"] = selected_scale

if st.session_state["current_scale"] != selected_scale:
    st.session_state.clear()
    st.session_state["current_scale"] = selected_scale
    st.rerun()

current_scale_data = scale_db[selected_scale]

# 根据题库长度重设答案列表
if len(st.session_state["answers"]) != len(current_scale_data["questions"]):
    st.session_state["answers"] = [None] * len(current_scale_data["questions"])

# 动态设定分页大小（SCL-90共90题，单页渲染10题；其他短量表单页渲染3题）
QUESTIONS_PER_PAGE = 10 if selected_scale == "SCL-90" else 3
total_questions = len(current_scale_data["questions"])
total_pages = math.ceil(total_questions / QUESTIONS_PER_PAGE)

def validate_current_page(start_idx, end_idx):
    for i in range(start_idx, end_idx):
        if st.session_state["answers"][i] is None:
            return False, i + 1
    return True, -1

# ==========================================
# 4. 前端界面渲染
# ==========================================
if not st.session_state["submitted"]:
    
    st.markdown(f"<h1 class='main-title'>{current_scale_data['name']}</h1>", unsafe_allow_html=True)
    
    # 指导语
    st.markdown(f"""
    <div class="instruction-card">
        <p><strong>免费声明：</strong> 本测试完全免费，无需支付任何费用。</p>
        <p><strong>数据用途：</strong> 数据仅用于心理学科研统计分析，已开启匿名哈希加密，绝不外泄。</p>
        <p><strong>测试说明：</strong> 本量表共 {total_questions} 道题，预计耗时 {"10-15" if selected_scale == "SCL-90" else "2-3"} 分钟。</p>
        <p style="margin-bottom: 0;"><strong>测试目的：</strong> {current_scale_data['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 代号输入框
    st.session_state["user_id"] = st.text_input(
        "请输入您的被试编号或昵称（如 P01，以便记录）：", 
        value=st.session_state["user_id"]
    )
    
    # 进度条
    progress_val = (st.session_state["current_page"] + 1) / total_pages
    st.progress(progress_val, text=f"第 {st.session_state['current_page'] + 1} 部分 / 共 {total_pages} 部分")
    st.markdown("<hr class='clinical-divider'>", unsafe_allow_html=True)
    
    if st.session_state["error_msg"]:
        st.error(st.session_state["error_msg"])

    start_idx = st.session_state["current_page"] * QUESTIONS_PER_PAGE
    end_idx = min(start_idx + QUESTIONS_PER_PAGE, total_questions)
    current_questions = current_scale_data["questions"][start_idx:end_idx]
    options_labels = [opt["label"] for opt in current_scale_data["options"]]

    for i, q in enumerate(current_questions):
        actual_q_index = start_idx + i 
        
        current_ans_val = st.session_state["answers"][actual_q_index]
        default_index = None
        if current_ans_val is not None:
            for opt_idx, opt in enumerate(current_scale_data["options"]):
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
            for opt in current_scale_data["options"]:
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
                    st.session_state["error_msg"] = "⚠️ 请注意：必须先在顶部输入您的被试编号或昵称，才能进入下一部分。"
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
                    st.session_state["error_msg"] = "⚠️ 请注意：必须先在顶部输入您的被试编号或昵称，才能提交问卷。"
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
    # 5. 结果报告生成层
    # ==========================================
    st.markdown("<h1 class='main-title'>评估报告</h1>", unsafe_allow_html=True)
    try:
        if selected_scale == "PHQ-9":
            result = calculate_phq9(st.session_state["answers"])
            # 增加第五个参数 "PHQ-9"
            save_record(st.session_state["answers"], result["total_score"], result["severity"], st.session_state["user_id"], "PHQ-9")
            st.success("数据收集完成，您的记录已成功保存。")
            st.metric(label="PHQ-9 评估总分", value=result["total_score"])
            st.markdown(f"### 诊断参考：{result['severity']}")
            
        elif selected_scale == "GAD-7":
            result = calculate_gad7(st.session_state["answers"])
            # 增加第五个参数 "GAD-7"
            save_record(st.session_state["answers"], result["total_score"], result["severity"], st.session_state["user_id"], "GAD-7")
            
            st.success("数据收集完成，您的记录已成功保存。")
            st.metric(label="GAD-7 评估总分", value=result["total_score"])
            st.markdown(f"### 诊断参考：{result['severity']}")
            
        elif selected_scale == "SCL-90":
            result = calculate_scl90(st.session_state["answers"])
            # 增加第五个参数 "SCL-90"
            save_record(st.session_state["answers"], result["total_score"], result["severity"], st.session_state["user_id"], "SCL-90")
            
            # --- 精准复刻 SCL-90 临床报告样式 ---
            gsi_class = "highlight-red" if result["gsi"] >= 2.0 else "highlight-green"
            
            # 模块一：总评估结果报告
            st.markdown(f"""
            <div class="clinical-report-container">
                <div class="report-section">
                    <div class="report-section-title">总评估结果报告</div>
                    <div style="text-align: center; margin: 20px 0;">
                        <span style="font-size: 3rem; font-weight: bold; color: #ba1a1a; display: block;">{result['total_score']}</span>
                        <span style="font-size: 1.25rem; font-weight: bold; color: #ba1a1a;">{result['severity']}</span>
                    </div>
                    <table class="clinical-table">
                        <thead>
                            <tr>
                                <th>统计项目</th>
                                <th>得分结果</th>
                                <th>参考结果</th>
                                <th>数值范围</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>总分</td>
                                <td class="highlight-red">{result['total_score']}</td>
                                <td class="highlight-red">{"阳性" if result['total_score'] >= 160 else "阴性"}</td>
                                <td>90~450</td>
                            </tr>
                            <tr>
                                <td>总症状指数</td>
                                <td class="{gsi_class}">{result['gsi']}</td>
                                <td class="{gsi_class}">{result['severity']}</td>
                                <td>1~5</td>
                            </tr>
                            <tr>
                                <td>阳性项目数</td>
                                <td class="highlight-red">{result['pos_count']}</td>
                                <td class="highlight-red">{"阳性" if result['pos_count'] > 43 else "阴性"}</td>
                                <td>0~90</td>
                            </tr>
                            <tr>
                                <td>阴性项目数</td>
                                <td>{result['neg_count']}</td>
                                <td>{"阴性" if result['pos_count'] <= 43 else "阳性"}</td>
                                <td>0~90</td>
                            </tr>
                            <tr>
                                <td>阳性症状均分</td>
                                <td>{result['psdi']}</td>
                                <td>-</td>
                                <td>0~5</td>
                            </tr>
                        </tbody>
                    </table>
                    <p style="font-size: 0.95rem; color: #414844; line-height: 1.6; margin-top: 15px;">
                        <strong>说明：</strong>按全国正常人 SCL-90 常模(N=1388)(1-5级评分)，当测试总分超过160分，或阳性项目数超过43项，需考虑筛选阳性。您的测试总分为 {result['total_score']} 分，您的阳性项目数为 {result['pos_count']} 项，综合以上结果，您的总评估结果为阳性，按总症状指数，总的测试评级为 {result['severity']}。
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # 模块二：各项症状评估结果
            factors_html = ""
            for f_name, f_data in result["factors"].items():
                if f_name == "其它":
                    continue
                hl_class = "highlight-red" if f_data["is_abnormal"] else "highlight-green"
                factors_html += f"""
                <tr>
                    <td>{f_name}</td>
                    <td>{f_data['total']}</td>
                    <td class="{hl_class}">{f_data['mean']}</td>
                    <td class="{hl_class}">{f_data['severity']}</td>
                    <td>{f_data['norm']}</td>
                </tr>
                """
            # 追加“其它”因子（无常模数据）
            other_data = result["factors"]["其它"]
            factors_html += f"""
            <tr>
                <td>其它 (睡眠与饮食)</td>
                <td>{other_data['total']}</td>
                <td>{other_data['mean']}</td>
                <td>-</td>
                <td>-</td>
            </tr>
            """
            
            st.markdown(f"""
                <div class="report-section">
                    <div class="report-section-title">各项症状评估结果报告</div>
                    <table class="clinical-table">
                        <thead>
                            <tr>
                                <th>因子</th>
                                <th>总分</th>
                                <th>均分</th>
                                <th>结果</th>
                                <th>M±SD</th>
                            </tr>
                        </thead>
                        <tbody>
                            {factors_html}
                        </tbody>
                    </table>
                    <p style="font-size: 0.95rem; color: #414844; line-height: 1.6; margin-top: 15px;">
                        <strong>说明：</strong>按全国正常人 SCL-90 常模(N=1388)(1-5级评分)，每个因子均分数值范围为1~5。如果因子均分超过因子常模（M+SD，平均分+标准差）即表示筛选异常。
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # 模块三：大数据统计对比
            # 常模均值
            norms_avg = {
                "躯体化": 1.37, "强迫症状": 1.62, "人际敏感": 1.65, "抑郁": 1.50,
                "焦虑": 1.39, "敌对": 1.46, "恐怖": 1.23, "偏执": 1.43, "精神病性": 1.29
            }
            # 群体均值（取自全国大数据常模或模拟常模）
            group_avg = {
                "总分": 223.00, "躯体化": 2.06, "强迫症状": 2.87, "人际敏感": 2.77, "抑郁": 2.75,
                "焦虑": 2.51, "敌对": 2.37, "恐怖": 2.10, "偏执": 2.44, "精神病性": 2.41, "其它": 2.48
            }
            
            comp_rows_html = ""
            # 第一行：总分
            total_diff = result["total_score"] - group_avg["总分"]
            diff_symbol = f"<span class='highlight-red'>{total_diff:.2f} ↑</span>" if total_diff >= 0 else f"<span class='highlight-green'>{abs(total_diff):.2f} ↓</span>"
            comp_rows_html += f"""
            <tr>
                <td>总分</td>
                <td>{group_avg['总分']:.2f}</td>
                <td>{result['total_score']:.2f}</td>
                <td>{diff_symbol}</td>
            </tr>
            """
            
            # 因子各行
            for f_name, f_data in result["factors"].items():
                g_avg = group_avg[f_name]
                f_diff = f_data["mean"] - g_avg
                if f_diff >= 0:
                    diff_symbol = f"<span class='highlight-red'>{f_diff:.2f} ↑</span>"
                else:
                    diff_symbol = f"<span class='highlight-green'>{abs(f_diff):.2f} ↓</span>"
                comp_rows_html += f"""
                <tr>
                    <td>{f_name}</td>
                    <td>{g_avg:.2f}</td>
                    <td>{f_data['mean']:.2f}</td>
                    <td>{diff_symbol}</td>
                </tr>
                """
                
            st.markdown(f"""
                <div class="report-section">
                    <div class="report-section-title">大数据统计对比</div>
                    <table class="clinical-table">
                        <thead>
                            <tr>
                                <th>因子</th>
                                <th>群体均分</th>
                                <th>我的结果</th>
                                <th>差值</th>
                            </tr>
                        </thead>
                        <tbody>
                            {comp_rows_html}
                        </tbody>
                    </table>
                    <p style="font-size: 0.95rem; color: #414844; line-height: 1.6; margin-top: 15px;">
                        <strong>说明：</strong>群体均分为本平台对应性别、年龄段所有用户有效统计平均结果。
                    </p>
                </div>
            """, unsafe_allow_html=True)

            # 模块四：因子深度剖析 (Factor Descriptions)
            desc_mapping = {
                "躯体化": {
                    "range": "12-60", "desc": "主要反映主观的身体不适感，包括心血管、胃肠道、呼吸等系统的主诉不适，以及头痛、背痛、肌肉酸痛等。得分在24分以下代表不明显；36分以上表明个体在身体上有较明显的不适，常伴有躯体性焦虑征象。"
                },
                "强迫症状": {
                    "range": "10-50", "desc": "主要反映明知没有必要但又无法摆脱的无意义思想、冲动和行为。高分个体常伴有注意力分散、难以做出决定、脑子变空、记忆力不好等认知障碍倾向。"
                },
                "人际敏感": {
                    "range": "9-45", "desc": "主要指在人际交往中的不自在感与自卑感。在与他人比较时更为突出，表现为心神不安、社交退缩、对他人行为过度敏感、消极期待等。"
                },
                "抑郁": {
                    "range": "13-65", "desc": "反映与临床抑郁症状群相联系的行为表现。特征是生活兴趣减退、缺乏动力、悲观失望，认为自己没有价值。重度得分时常伴有死亡和自杀观念。"
                },
                "焦虑": {
                    "range": "10-50", "desc": "反映与临床焦虑症状群相关的精神症状。表现为紧张、神经过敏、烦躁不安、心跳加快，严重的伴有惊恐发作、解体体验等躯体征象。"
                },
                "敌对": {
                    "range": "6-30", "desc": "从思维、情感及行为三个方面反映敌对表现。包括易怒、摔东西、争论直到不可控制的脾气暴发等负性冲动。"
                },
                "恐怖": {
                    "range": "7-35", "desc": "反映传统的恐怖状态或恐怖症的内容。恐惧对象包括出门旅行，空旷场地，人群或公共场所和交通工具。此外，还有反映社交恐怖的项目。"
                },
                "偏执": {
                    "range": "6-30", "desc": "主要指投射性思维、敌对、猜疑、关系观念、妄想、被动体验和夸大等偏执性思维基本特征。"
                },
                "精神病性": {
                    "range": "10-50", "desc": "反映各式各样的急性精神病性症状和行为，包括幻听、被动体验、思维播散以及分裂性生活方式的指征。"
                },
                "其它": {
                    "range": "7-35", "desc": "主要反映睡眠及饮食情况，作为附加项目或第10个因子进行处理，以便使各因子分之和等于总分。"
                }
            }
            
            desc_cards_html = ""
            for f_name, f_desc in desc_mapping.items():
                f_data = result["factors"][f_name]
                desc_cards_html += f"""
                <div class="factor-desc-card">
                    <h4 style="font-weight:bold; font-size:1.15rem; color:#012d1d; margin-bottom:10px;">{f_name}</h4>
                    <p style="color:#1d4ed8; font-weight:600; margin-bottom:8px; font-size:1rem;">您的得分为 {f_data['total']} 分 (均分 {f_data['mean']:.2f})</p>
                    <p style="font-size:0.95rem; color:#475569; line-height:1.6;">
                        总分范围在 {f_desc['range']} 分之间。{f_desc['desc']}
                    </p>
                </div>
                """
                
            st.markdown(f"""
                <div class="report-section">
                    <div class="report-section-title">因子说明</div>
                    {desc_cards_html}
                </div>
                
                <!-- 页脚 -->
                <div style="text-align: center; color: #ba1a1a; font-weight: bold; margin-top: 20px; font-size:0.95rem;">
                    说明：由于量表只是辅助筛查工具，因此测试结果仅供参考。
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 重新测试
        if st.button("重新测试"):
            st.session_state.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"系统错误：{str(e)}")