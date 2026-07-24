from typing import List, Dict, Any

def calculate(scores: List[int]) -> Dict[str, Any]:
    """PHQ-9 独立算法与报告"""
    if len(scores) != 9:
        raise ValueError(f"PHQ-9 必须包含 9 道题的回答，当前收到 {len(scores)} 题")
    
    total_score = sum(scores)
    
    if total_score <= 4:
        severity = "没有至轻微抑郁倾向"
        suggestion = "您的得分在正常范围内。您目前的心理防御机制运作良好。请继续保持现有的生活节奏，适度放松，享受生活。"
    elif total_score <= 9:
        severity = "轻度抑郁倾向"
        suggestion = "您的得分反映出轻微的抑郁倾向。建议关注近期情绪波动，适度运动、倾诉或通过书写日记释放压力。"
    elif total_score <= 14:
        severity = "中度抑郁倾向"
        suggestion = "您的得分反映出中等程度的抑郁倾向。建议安排一次专业的心理咨询（如认知行为疗法 CBT）来梳理当前的情绪压力。平时可尝试增加户外运动和规律作息。"
    elif total_score <= 19:
        severity = "中重度抑郁倾向"
        suggestion = "您的得分反映出较明显的抑郁症状。建议您寻找专业的心理学从业人员或前往精神医学科进行专业评估和干预。"
    else:
        severity = "重度抑郁倾向"
        suggestion = "您的得分反映出强烈的抑郁症状。这可能会严重影响您的日常功能、睡眠和食欲。请您务必尽快前往专业的三甲医院精神心理科就诊，寻求药物干预与专业的心理咨询。"
        
    # 生成该量表专属的 HTML 报告
    html_report = f"""
    <div class="clinical-report-container">
        <div class="report-section">
            <div class="report-section-title">评估结果报告</div>
            <div style="text-align: center; margin: 20px 0;">
                <span style="font-size: 3rem; font-weight: bold; color: #ba1a1a; display: block;">{total_score}</span>
                <span style="font-size: 1.25rem; font-weight: bold; color: #ba1a1a;">{severity}</span>
            </div>
            <div style="margin-top: 20px; line-height: 1.8;">
                <p><strong>详细说明：</strong>{suggestion}</p>
            </div>
        </div>
    </div>
    """
    
    return {
        "total_score": total_score,
        "severity": severity,
        "html_report": html_report,
        "csv_header": "评估量表,PHQ-9 抑郁筛查量表\n",
        "csv_rows": f"总分,{total_score},{severity},-\n"
    }