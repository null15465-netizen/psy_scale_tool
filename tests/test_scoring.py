import pytest
from logic.scoring import calculate_phq9

def test_calculate_phq9_min_score():
    """测试极端情况 1：患者全部选最低分，总分应为 0"""
    answers = [0, 0, 0, 0, 0, 0, 0, 0, 0] # 9个0
    result = calculate_phq9(answers)
    assert result["total_score"] == 0
    assert result["severity"] == "没有至轻微抑郁倾向"

def test_calculate_phq9_max_score():
    """测试极端情况 2：患者全部选最高分，总分应为 27"""
    answers = [3] * 9  # 简写：生成9个3的列表
    result = calculate_phq9(answers)
    assert result["total_score"] == 27
    assert result["severity"] == "重度抑郁倾向"

def test_calculate_phq9_invalid_length():
    """测试质量门禁 1：如果传入的答案少于 9 个，系统必须抛出错误并拦截"""
    answers = [1, 2, 3] # 只有 3 个答案
    # 下面这行的意思是：断言（确保）接下来的代码一定会引发 ValueError，否则测试失败
    with pytest.raises(ValueError, match="必须包含 9 道题"):
        calculate_phq9(answers)

def test_calculate_phq9_invalid_value():
    """测试质量门禁 2：如果传入了超纲的分数（比如 4分），系统必须拦截"""
    answers = [0, 1, 2, 3, 4, 0, 1, 2, 3] # 包含了一个非法的 4
    with pytest.raises(ValueError, match="在 0 到 3 之间"):
        calculate_phq9(answers)