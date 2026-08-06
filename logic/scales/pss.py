import json
import os
from typing import List, Dict, Any


def _load_questions() -> List[Dict[str, Any]]:
    """读取题库，用于把分值还原为选项文字。"""
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "scales.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["PSS"]["questions"]


_QUESTIONS = _load_questions()


def _value_text(q: Dict[str, Any], value: Any) -> str:
    """把答案还原为可读文字：文本题返回原文，选择题返回选项标签。"""
    if isinstance(value, str):
        return value
    if value is None:
        return "未作答"
    for opt in q.get("options", []):
        if opt["score"] == value:
            return opt["label"]
    return str(value)


def _section_sum(values: List[Any]) -> int:
    """只统计已作答的整数分值，跳过题与文本题不计入。"""
    return sum(v for v in values if isinstance(v, int))


def _answered(values: List[Any]) -> int:
    """统计已作答的题数（文本题作答也算）。"""
    return sum(1 for v in values if v is not None and v != "")


def calculate(answers: List[Any]) -> Dict[str, Any]:
    """精神科医护人员工作压力与心理健康调查问卷。
    共 68 题：基本信息 7 题 + WVS 5 题 + PCL-5 20 题 + BHS 5 题 + PTCI 7 题 + SPOS 24 题。
    允许跳过未作答题目（None 或空字符串）。"""
    if len(answers) != 68:
        raise ValueError(f"本问卷必须包含 68 道题的回答，当前收到 {len(answers)} 题")

    demo = answers[0:7]
    wvs = answers[7:12]
    pcl = answers[12:32]
    bhs = answers[32:37]
    ptci = answers[37:44]
    spos = answers[44:68]

    wvs_total = _section_sum(wvs)
    pcl_total = _section_sum(pcl)
    bhs_total = _section_sum(bhs)
    ptci_total = _section_sum(ptci)
    spos_total = _section_sum(spos)
    total_score = wvs_total + pcl_total + bhs_total + ptci_total + spos_total

    skip_count = 68 - sum(_answered(s) for s in [demo, wvs, pcl, bhs, ptci, spos])
    severity = "全部完成" if skip_count == 0 else f"完成（跳过 {skip_count} 题）"

    demo_labels = ["性别", "年龄", "所在科室", "工作年限", "职务", "职称", "聘用形式"]
    demo_html = "".join(
        f"<tr><td style='text-align:left;'>{demo_labels[i]}</td><td>{_value_text(_QUESTIONS[i], answers[i])}</td></tr>"
        for i in range(7)
    )

    def section_block(title: str, total: int, answered: int, note: str) -> str:
        return f"""
        <div class="report-section">
            <div class="report-section-title">{title}</div>
            <p>已作答 {answered} 题，合计 {total} 分。</p>
            <p style="font-size:0.95rem; color:#a9b8ad; margin-top:8px;">{note}</p>
        </div>"""

    pcl_note = (
        "PCL-5 总分范围为 0-80 分，33 分及以上常作为创伤后应激症状的筛查界值，"
        "提示可能需要进一步专业评估。本结果仅用于研究，不构成临床诊断。"
    )
    html_report = f"""
    <div class="clinical-report-container">
        <div class="report-section">
            <div class="report-section-title">第一部分 基本信息</div>
            <table class="clinical-table"><tbody>{demo_html}</tbody></table>
        </div>
        {section_block("第二部分 工作中的暴力经历（WVS）", wvs_total, _answered(wvs), "WVS 总分为 0-15 分，得分越高表示过去 12 个月遭受的工作场所暴力事件越多。")}
        {section_block("第三部分 心理困扰（PCL-5）", pcl_total, _answered(pcl), pcl_note)}
        {section_block("第四部分 注意与警觉（BHS）", bhs_total, _answered(bhs), "BHS 总分为 5-25 分，得分越高表示越处于警觉与戒备状态。本结果仅用于研究。")}
        {section_block("第五部分 对世界的看法（PTCI 负向认知分量表）", ptci_total, _answered(ptci), "PTCI 分量表总分为 7-49 分，得分越高表示对世界的负向认知越强。本结果仅用于研究。")}
        {section_block("第六部分 组织支持（SPOS）", spos_total, _answered(spos), "SPOS 总分为 24-144 分，得分越高表示感知到的组织支持越多。本结果仅用于研究。")}
        <div class="report-section">
            <div class="report-section-title">填写说明</div>
            <p>本问卷共有 68 道题，您已完成 {68 - skip_count} 题，跳过 {skip_count} 题。</p>
            <p style="font-size:0.95rem; color:#a9b8ad; margin-top:8px;">如本问卷让您感到任何不适，请及时联系医院心理援助部门或拨打心理援助热线（如 12356）。</p>
        </div>
    </div>
    """

    csv_header = "量表名称,部分,题号,题目,答案,分值\n"
    csv_rows = ""
    sections = [
        ("第一部分 基本信息", demo, 0),
        ("第二部分 工作中的暴力经历（WVS）", wvs, 7),
        ("第三部分 心理困扰（PCL-5）", pcl, 12),
        ("第四部分 注意与警觉（BHS）", bhs, 32),
        ("第五部分 对世界的看法（PTCI）", ptci, 37),
        ("第六部分 组织支持（SPOS）", spos, 44),
    ]
    for sec_name, sec, start in sections:
        for j, v in enumerate(sec):
            q = _QUESTIONS[start + j]
            if v is None or v == "":
                continue
            csv_rows += (
                f"精神科医护调查,{sec_name},{q['id']},{q['text']},"
                f"{_value_text(q, v)},{v if isinstance(v, int) else ''}\n"
            )

    return {
        "total_score": total_score,
        "severity": severity,
        "html_report": html_report,
        "csv_header": csv_header,
        "csv_rows": csv_rows,
    }
