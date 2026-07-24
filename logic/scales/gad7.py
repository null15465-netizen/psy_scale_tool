from typing import List, Dict, Any

def calculate(scores: List[int]) -> Dict[str, Any]:
    """GAD-7 独立算法与报告"""
    if len(scores) != 7:
        raise ValueError(f"GAD-7 必须包含 7 道题的回答，当前收到 {len(scores)} 题")
    
    total_score = sum(scores)
    
    if total_score <= 4:
        severity = "没有至轻微焦虑倾向"
        suggestion = "您的得分在正常范围内。您目前能较好地应对日常生活中的压力。请继续保持轻松的心态。"
    elif total_score <= 9:
        severity = "轻度焦虑倾向"
        suggestion = "您的得分反映出轻微的焦虑情绪。可能由于近期生活、工作或学习压力较大。建议尝试深呼吸、正念冥想或户外散步来缓解紧张感。"
    elif total_score <= 14:
        severity = "中度焦虑倾向"
        suggestion = "您的得分反映出中等程度的焦虑状态。建议您寻求心理咨询师的帮助，学习焦虑管理技术，避免焦虑情绪进一步影响生理健康（如引发失眠等）。"
    else:
        severity = "重度焦虑倾向"
        suggestion = "您的得分反映出强烈的焦虑症状，这可能已经显著影响了您的日常生活。建议您尽快前往专业医院心理科或精神科就诊，结合药物与专业治疗恢复心理平衡。"

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
        "csv_header": "评估量表,GAD-7 广泛性焦虑量表\n",
        "csv_rows": f"总分,{total_score},{severity},-\n"
    }