from typing import List, Dict, Any

def calculate(scores: List[int]) -> Dict[str, Any]:
    """SAS 算法与报告生成"""
    if len(scores) != 20:
        raise ValueError(f"SAS 必须包含 20 道题的回答，当前收到 {len(scores)} 题")
    
    # 1-based 反向计分题号
    reverse_items = {5, 9, 13, 17, 19}
    
    raw_scores = []
    for idx, s in enumerate(scores):
        item_num = idx + 1
        if item_num in reverse_items:
            raw_scores.append(5 - s)
        else:
            raw_scores.append(s)
            
    raw_total = sum(raw_scores)
    standard_score = int(raw_total * 1.25)
    
    # 中国常模划分标准
    if standard_score < 50:
        severity = "无焦虑症状"
        suggestion = "您的分值在正常范围内，目前情绪状态放松稳定。请继续保持心理弹性。"
    elif standard_score <= 59:
        severity = "轻度焦虑"
        suggestion = "您的分值处于轻度焦虑范围。多由生活细节和临时压力诱发。建议尝试深呼吸、正念冥想、或者减少咖啡因摄入。"
    elif standard_score <= 69:
        severity = "中度焦虑"
        suggestion = "您的分值处于中度焦虑范围。建议您寻求心理咨询师的引导，学习情绪调节技巧，防止焦虑影响生理指标。"
    else:
        severity = "重度焦虑"
        suggestion = "您的分值处于重度焦虑范围，建议您尽快寻求心理科或精神科专科医师的诊疗帮助，结合物理或药物干预缓解躯体焦虑不适。"

    html_report = f"""
    <div class="clinical-report-container">
        <div class="report-section">
            <div class="report-section-title">评估结果报告</div>
            <div style="text-align: center; margin: 20px 0;">
                <span style="font-size: 3rem; font-weight: bold; color: #ba1a1a; display: block;">{standard_score}</span>
                <span style="font-size: 1.25rem; font-weight: bold; color: #ba1a1a;">{severity} (标准分)</span>
            </div>
            <div style="margin-top: 20px; line-height: 1.8;">
                <p><strong>原始得分：</strong>{raw_total} 分（转化后标准分为 {standard_score} 分，临界值为 50 分）</p>
                <p><strong>详细说明：</strong>{suggestion}</p>
            </div>
        </div>
    </div>
    """

    return {
        "total_score": standard_score,
        "severity": severity,
        "html_report": html_report,
        "csv_header": "评估量表,焦虑自评量表 (SAS)\n",
        "csv_rows": f"原始分,{raw_total},标准分,{standard_score},评估结果,{severity}\n"
    }