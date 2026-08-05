from typing import List, Dict, Any

def calculate(scores: List[int]) -> Dict[str, Any]:
    """SCL-90 独立算法与庞大临床报告生成"""
    if len(scores) != 90:
        raise ValueError(f"SCL-90 必须包含 90 道题的回答，当前收到 {len(scores)} 题")

    total_score = sum(scores)
    gsi = round(total_score / 90.0, 2)
    pos_count = sum(1 for s in scores if s >= 2)
    neg_count = sum(1 for s in scores if s == 1)
    psdi = round((total_score - neg_count) / pos_count, 2) if pos_count > 0 else 1.0

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

    norms = {
        "躯体化": (1.37, 0.48), "强迫症状": (1.62, 0.58), "人际敏感": (1.65, 0.61),
        "抑郁": (1.50, 0.59), "焦虑": (1.39, 0.43), "敌对": (1.46, 0.55),
        "恐怖": (1.23, 0.41), "偏执": (1.43, 0.57), "精神病性": (1.29, 0.42)
    }

    group_avg = {
        "总分": 223.00, "躯体化": 2.06, "强迫症状": 2.87, "人际敏感": 2.77, "抑郁": 2.75,
        "焦虑": 2.51, "敌对": 2.37, "恐怖": 2.10, "偏执": 2.44, "精神病性": 2.41, "其它": 2.48
    }

    factors_report = {}
    factors_html = ""
    csv_rows = f"总分,{total_score},{severity},-\n"

    for factor_name, questions in factor_mapping.items():
        factor_scores = [scores[q_id - 1] for q_id in questions]
        f_total = sum(factor_scores)
        f_mean = round(f_total / len(questions), 2)
        
        if f_mean < 2.0:
            f_severity = "无症状"
        elif f_mean < 3.0:
            f_severity = "轻度"
        elif f_mean < 4.0:
            f_severity = "中度"
        else:
            f_severity = "重度"

        is_abnormal = False
        norm_str = "-"
        if factor_name in norms:
            m, sd = norms[factor_name]
            norm_str = f"{m}±{sd}"
            if f_mean > (m + sd):
                is_abnormal = True

        factors_report[factor_name] = {
            "total": f_total,
            "mean": f_mean,
            "severity": f_severity,
            "norm": norm_str,
            "is_abnormal": is_abnormal
        }

        # 拼接因子 HTML
        if factor_name != "其它":
            hl_class = "highlight-red" if is_abnormal else "highlight-green"
            factors_html += f"<tr><td>{factor_name}</td><td>{f_total}</td><td class='{hl_class}'>{f_mean:.2f}</td><td class='{hl_class}'>{f_severity}</td><td>{norm_str}</td></tr>"
            csv_rows += f"因子: {factor_name},{f_total},{f_mean:.2f},{f_severity}\n"

    # 追加其它因子到表格
    other_data = factors_report["其它"]
    factors_html += f"<tr><td>其它 (睡眠与饮食)</td><td>{other_data['total']}</td><td>{other_data['mean']:.2f}</td><td>-</td><td>-</td></tr>"
    csv_rows += f"因子: 其它,{other_data['total']},{other_data['mean']:.2f},-\n"

    # 拼接大数据对比 HTML
    comp_rows_html = ""
    total_diff = total_score - group_avg["总分"]
    diff_symbol = f"<span class='highlight-red'>{total_diff:.2f} 向上箭头</span>" if total_diff >= 0 else f"<span class='highlight-green'>{abs(total_diff):.2f} 向下箭头</span>"
    comp_rows_html += f"<tr><td>总分</td><td>{group_avg['总分']:.2f}</td><td>{total_score:.2f}</td><td>{diff_symbol}</td></tr>"
    
    for f_name, f_data in factors_report.items():
        g_avg = group_avg[f_name]
        f_diff = f_data["mean"] - g_avg
        diff_symbol = f"<span class='highlight-red'>{f_diff:.2f} 向上箭头</span>" if f_diff >= 0 else f"<span class='highlight-green'>{abs(f_diff):.2f} 向下箭头</span>"
        comp_rows_html += f"<tr><td>{f_name}</td><td>{g_avg:.2f}</td><td>{f_data['mean']:.2f}</td><td>{diff_symbol}</td></tr>"

    # 拼接因子深度剖析 HTML
    desc_mapping = {
        "躯体化": {"range": "12-60", "desc": "主要反映主观的身体不适感，包括心血管等系统的主诉不适及疼痛。得分在36分以上表明躯体上有较明显不适。"},
        "强迫症状": {"range": "10-50", "desc": "反映临床上的强迫症状群，如强迫观念和仪式行为。高分个体常伴有注意力涣散、决策困难等认知阻碍。"},
        "人际敏感": {"range": "9-45", "desc": "反映人际交往中的不自在和自卑感。在与他人比较时更为突出，表现为社交退缩、对他人言行过度敏感。"},
        "抑郁": {"range": "13-65", "desc": "反映抑郁发作的精神状态，如悲观失望、缺乏动力、无价值感。"},
        "焦虑": {"range": "10-50", "desc": "反映临床焦虑特征，如坐立不安、神经过敏、心跳加快等躯体焦虑征象。"},
        "敌对": {"range": "6-30", "desc": "从思维、情感和行为上反映敌对表现，如易怒、摔东西、冲动。"},
        "恐怖": {"range": "7-35", "desc": "反映传统的恐怖症状态，如害怕乘车、人群、高空等特定场合。"},
        "偏执": {"range": "6-30", "desc": "主要反映猜疑、妄想、被动体验和夸大等偏执性思维基本特征。"},
        "精神病性": {"range": "10-50", "desc": "反映幻听、被动体验、思维播散等急性精神病性临床症状。"},
        "其它": {"range": "7-35", "desc": "主要反映睡眠及饮食情况，作为附加项目参与计分平衡。"}
    }
    desc_cards_html = ""
    for f_name, f_desc in desc_mapping.items():
        f_data = factors_report[f_name]
        desc_cards_html += f"<div class='factor-desc-card'><h4 style='font-weight:bold; font-size:1.15rem; color:#f1ede1; margin-bottom:10px;'>{f_name}</h4><p style='color:#a8bfae; font-weight:600; margin-bottom:8px; font-size:1rem;'>您的得分为 {f_data['total']} 分 (均分 {f_data['mean']:.2f})</p><p style='font-size:0.95rem; color:#a9b8ad; line-height:1.6;'>总分范围在 {f_desc['range']} 分之间。{f_desc['desc']}</p></div>"

    gsi_class = "highlight-red" if gsi >= 2.0 else "highlight-green"

    html_report = f"""
    <div class="clinical-report-container">
        <div class="report-section">
            <div class="report-section-title">总评估结果报告</div>
            <div style="text-align: center; margin: 20px 0;">
                <span style="font-size: 3rem; font-weight: bold; color: #ba1a1a; display: block;">{total_score}</span>
                <span style="font-size: 1.25rem; font-weight: bold; color: #ba1a1a;">{severity}</span>
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
                    <tr><td>总分</td><td class="highlight-red">{total_score}</td><td class="highlight-red">{"阳性" if total_score >= 160 else "阴性"}</td><td>90~450</td></tr>
                    <tr><td>总症状指数</td><td class="{gsi_class}">{gsi}</td><td class="{gsi_class}">{severity}</td><td>1~5</td></tr>
                    <tr><td>阳性项目数</td><td class="highlight-red">{pos_count}</td><td class="highlight-red">{"阳性" if pos_count > 43 else "阴性"}</td><td>0~90</td></tr>
                    <tr><td>阴性项目数</td><td>{neg_count}</td><td>{"阴性" if pos_count <= 43 else "阳性"}</td><td>0~90</td></tr>
                    <tr><td>阳性症状均分</td><td>{psdi}</td><td>-</td><td>0~5</td></tr>
                </tbody>
            </table>
            <p style="font-size: 0.95rem; color: #a9b8ad; line-height: 1.6; margin-top: 15px;">
                <strong>说明：</strong>按全国正常人 SCL-90 常模(N=1388)(1-5级评分)，当测试总分超过160分，或阳性项目数超过43项，需考虑筛选阳性。您的测试总分为 {total_score} 分，您的阳性项目数为 {pos_count} 项，综合以上结果，您的总评估结果为阳性，按总症状指数，总的测试评级为 {severity}。
            </p>
        </div>
        
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
        </div>
        
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
        </div>
        
        <div class="report-section">
            <div class="report-section-title">因子说明</div>
            {desc_cards_html}
        </div>
    </div>
    """

    return {
        "total_score": total_score,
        "severity": severity,
        "html_report": html_report,
        "csv_header": "评估量表,症状自评量表 (SCL-90)\n",
        "csv_rows": csv_rows
    }
