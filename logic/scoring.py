from typing import List, Dict, Union

def calculate_phq9(scores: List[int]) -> Dict[str, Union[int, str]]:
    if len(scores) != 9:
        raise ValueError(f"PHQ-9 必须包含 9 道题的回答，当前收到 {len(scores)} 题")
    if any(s < 0 or s > 3 for s in scores):
        raise ValueError("PHQ-9 单题分数必须在 0 到 3 之间")
    total_score = sum(scores)
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
    return {"total_score": total_score, "severity": severity}

def calculate_gad7(scores: List[int]) -> Dict[str, Union[int, str]]:
    if len(scores) != 7:
        raise ValueError(f"GAD-7 必须包含 7 道题的回答，当前收到 {len(scores)} 题")
    if any(s < 0 or s > 3 for s in scores):
        raise ValueError("GAD-7 单题分数必须在 0 到 3 之间")
    total_score = sum(scores)
    if total_score <= 4:
        severity = "没有至轻微焦虑倾向"
    elif total_score <= 9:
        severity = "轻度焦虑倾向"
    elif total_score <= 14:
        severity = "中度焦虑倾向"
    else:
        severity = "重度焦虑倾向"
    return {"total_score": total_score, "severity": severity}

def calculate_scl90(scores: List[int]) -> Dict[str, Union[int, float, str, dict]]:
    """
    计算 SCL-90 临床指标、因子均分及严重程度。
    """
    if len(scores) != 90:
        raise ValueError(f"SCL-90 必须包含 90 道题的回答，当前收到 {len(scores)} 题")
    if any(s < 1 or s > 5 for s in scores):
        raise ValueError("SCL-90 单题分数必须在 1 到 5 之间")

    total_score = sum(scores)
    gsi = round(total_score / 90.0, 2)  # 总症状指数 (总均分)
    pos_count = sum(1 for s in scores if s >= 2)  # 阳性项目数
    neg_count = sum(1 for s in scores if s == 1)  # 阴性项目数
    psdi = round((total_score - neg_count) / pos_count, 2) if pos_count > 0 else 1.0  # 阳性症状均分

    # 总分评级（GSI 判定）
    if gsi < 2.0:
        severity = "无明显症状"
    elif gsi < 2.5:
        severity = "轻度"
    elif gsi < 3.5:
        severity = "轻度~中度"
    elif gsi < 4.5:
        severity = "中度~重度"
    else:
        severity = "重度"

    # 十大因子结构划分 (题号转为 0-based 索引)
    factor_mapping = {
        "躯体化": [1, 4, 12, 27, 40, 42, 48, 49, 52, 53, 56, 58],
        "强迫症状": [3, 9, 10, 28, 38, 45, 46, 51, 55, 65],
        "人际敏感": [6, 21, 34, 36, 37, 41, 61, 69, 73],
        "抑郁": [5, 14, 15, 20, 22, 26, 29, 30, 31, 32, 54, 71, 79],
        "焦虑": [2, 17, 23, 33, 39, 57, 72, 78, 80, 86],
        "敌对": [11, 24, 63, 67, 74, 81],
        "恐怖": [13, 25, 47, 50, 70, 75, 82],
        "偏执": [8, 18, 43, 68, 76, 83],
        "精神病性": [7, 16, 35, 62, 77, 84, 85, 87, 88, 90],
        "其它": [19, 44, 59, 60, 64, 66, 89]
    }

    # 因子常模对照值 (M, SD)
    norms = {
        "躯体化": (1.37, 0.48),
        "强迫症状": (1.62, 0.58),
        "人际敏感": (1.65, 0.61),
        "抑郁": (1.50, 0.59),
        "焦虑": (1.39, 0.43),
        "敌对": (1.46, 0.55),
        "恐怖": (1.23, 0.41),
        "偏执": (1.43, 0.57),
        "精神病性": (1.29, 0.42)
    }

    factors_report = {}
    for factor_name, questions in factor_mapping.items():
        factor_scores = [scores[q_id - 1] for q_id in questions]
        f_total = sum(factor_scores)
        f_mean = round(f_total / len(questions), 2)
        
        # 严重度划分
        if f_mean < 2.0:
            f_severity = "无症状"
        elif f_mean < 3.0:
            f_severity = "轻度"
        elif f_mean < 4.0:
            f_severity = "中度"
        else:
            f_severity = "重度"

        # 判断是否超过常模 M+SD (临床筛选阳性标志)
        is_abnormal = False
        if factor_name in norms:
            m, sd = norms[factor_name]
            if f_mean > (m + sd):
                is_abnormal = True

        factors_report[factor_name] = {
            "total": f_total,
            "mean": f_mean,
            "severity": f_severity,
            "norm": f"{norms[factor_name][0]}±{norms[factor_name][1]}" if factor_name in norms else "-",
            "is_abnormal": is_abnormal
        }

    return {
        "total_score": total_score,
        "gsi": gsi,
        "pos_count": pos_count,
        "neg_count": neg_count,
        "psdi": psdi,
        "severity": severity,
        "factors": factors_report
    }