import pytest
from logic.scales.pss import calculate


def _full_answers(demo_vals, wvs_vals, pcl_vals, bhs_vals, ptci_vals, spos_vals):
    return demo_vals + wvs_vals + pcl_vals + bhs_vals + ptci_vals + spos_vals


def test_pss_min_score():
    answers = _full_answers(
        [1, 1, "精神科", 1, 1, 1, 1],
        [0] * 5,
        [0] * 20,
        [1] * 5,
        [1] * 7,
        [1] * 24,
    )
    result = calculate(answers)
    assert result["total_score"] == 36  # 基本信息不计分
    assert result["severity"] == "全部完成"


def test_pss_max_score():
    answers = _full_answers(
        [2, 3, "", 5, 6, 4, 3],
        [3] * 5,
        [4] * 20,
        [5] * 5,
        [7] * 7,
        [6] * 24,
    )
    result = calculate(answers)
    assert result["total_score"] == 15 + 80 + 25 + 49 + 144


def test_pss_allow_skip():
    answers = _full_answers(
        [None, None, "", None, None, None, None],
        [None] * 5,
        [None] * 20,
        [1] * 5,
        [None] * 7,
        [None] * 24,
    )
    result = calculate(answers)
    assert result["severity"].startswith("完成（跳过")
    assert result["total_score"] == 5


def test_pss_invalid_length():
    with pytest.raises(ValueError, match="必须包含 68 道题"):
        calculate([0])
