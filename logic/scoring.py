from typing import List, Dict, Union

def calculate_phq9(scores: List[int]) -> Dict[str, Union[int, str]]:
    """
    纯函数：计算 PHQ-9 得分并返回临床诊断建议。
    :param scores: 用户选择的分数列表，必须包含 9 个整数（每个范围 0-3）
    :return: 包含 'total_score' 和 'severity' 的字典
    """
    # 质量门禁：如果传入的答案不是9个，或者有超纲的分数，直接抛出系统错误
    if len(scores) != 9:
        raise ValueError(f"PHQ-9 必须包含 9 道题的回答，当前收到 {len(scores)} 题")
    if any(s < 0 or s > 3 for s in scores):
        raise ValueError("PHQ-9 单题分数必须在 0 到 3 之间")

    total_score = sum(scores)
    
    # 临床严重程度判定逻辑
    if total_score <= 4:
        severity = "没有至轻微抑郁倾向"
    elif total_score <= 9:
        severity = "轻度抑郁倾向"
    elif total_score <= 14:
        severity = "中度抑郁倾向"
    elif total_score <= 19:
        severity = "中重度抑郁倾向"
    else:
        severity = "重度抑郁倾向"
        
    return {
        "total_score": total_score,
        "severity": severity
    }