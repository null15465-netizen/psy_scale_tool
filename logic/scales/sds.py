from typing import List, Dict, Any

def calculate(scores: List[int]) -> Dict[str, Any]:
    """SDS 算法与报告生成"""
    if len(scores) != 20:
        raise ValueError(f"SDS 必须包含 20 道题的回答，当前收到 {len(scores)} 题")
    
    # 1-based 反向计分题号
    reverse_items = {2, 5, 6, 11, 12, 14, 16, 17, 18, 20}
    
    # 计算原始分并翻转反向题分数
    raw_scores = []
    for idx, s in enumerate(scores):
        item_num = idx + 1
        if item_num in reverse_items:
            # 1->4, 2->3, 3->2, 4->1
            raw_scores.append(5 - s)
        else:
            raw_scores.append(s)
            
    raw_total = sum(raw_scores)
    # 计算标准分 (乘以1.25取整)
    standard_score = int(raw_total * 1.25)
    
    # 中国常模划分标准
    if standard_score < 50:
        severity = "无抑郁症状"
        suggestion = "您的分值在正常范围内，目前情绪状态良好，请继续保持健康的生活习惯。"
    elif standard_score <= 59:
        severity = "轻度抑郁"
        suggestion = "您的分值处于轻度抑郁范围。可能是近期压力过载导致的短暂负性状态，建议多与人交流、适度倾诉，并进行户外放松。"
    elif standard_score <= 69:
        severity = "中度抑郁"
        suggestion = "您的分值处于中度抑郁范围。建议您安排一次专业的心理咨询（如认知行为疗法 CBT）以防情绪恶化。若持续无好转，请及时就医。"
    else:
        severity = "重度抑郁"
        suggestion = "您的分值处于重度抑郁范围。这可能已严重阻碍了您的日常生活、睡眠与社交功能。建议您尽快前往专业精神医学科就诊，寻求专业干预与支持。"

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
        "csv_header": "评估量表,抑郁自评量表 (SDS)\n",
        "csv_rows": f"原始分,{raw_total},标准分,{standard_score},评估结果,{severity}\n"
    }