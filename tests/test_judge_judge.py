import pytest
from app.judge.judge import JudgeResult, _aggregate, judge_submission
from app.judge.runner import CaseResult
def _cr(case_id: str, result: str, score: int, time_used: float = 0.1) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        result=result,
        score=score if result == "AC" else 0,
        time_used=time_used,
        exit_code=0 if result == "AC" else 1,
        stdout="",
        stderr="",
        is_hidden=False,
        message="",
    )
def test_aggregate_all_ac():
    cases = [_cr("c1", "AC", 50), _cr("c2", "AC", 50)]
    r = _aggregate(cases)
    assert r.final_result == "AC"
    assert r.total_score == 100
def test_aggregate_one_wa():
    cases = [_cr("c1", "AC", 50), _cr("c2", "WA", 50)]
    r = _aggregate(cases)
    assert r.final_result == "WA"
    assert r.total_score == 50
def test_aggregate_se_overrides_others():
    cases = [_cr("c1", "AC", 50), _cr("c2", "SE", 50), _cr("c3", "WA", 50)]
    r = _aggregate(cases)
    assert r.final_result == "SE"
    assert r.total_score == 50
def test_aggregate_tle_beats_re_and_wa():
    cases = [_cr("c1", "WA", 50), _cr("c2", "RE", 50), _cr("c3", "TLE", 50)]
    r = _aggregate(cases)
    assert r.final_result == "TLE"
def test_aggregate_re_beats_wa():
    cases = [_cr("c1", "WA", 50), _cr("c2", "RE", 50)]
    r = _aggregate(cases)
    assert r.final_result == "RE"
def test_aggregate_empty_cases_returns_se():
    r = _aggregate([])
    assert r.final_result == "SE"
    assert r.total_score == 0
def test_aggregate_total_time_is_sum():
    cases = [_cr("c1", "AC", 50, time_used=0.12), _cr("c2", "AC", 50, time_used=0.08)]
    r = _aggregate(cases)
    assert r.total_time == pytest.approx(0.2, abs=1e-6)
SIMPLE_ADD = "a, b = map(int, input().split())\nprint(a + b)\n"
WRONG = "print(0)\n"
DIVZERO = "print(1 / 0)\n"
async def test_judge_all_ac():
    test_cases = [
        {"case_id": "c1", "input": "1 2\n", "output": "3\n", "score": 50, "is_hidden": False},
        {"case_id": "c2", "input": "10 20\n", "output": "30\n", "score": 50, "is_hidden": True},
    ]
    r = await judge_submission(SIMPLE_ADD, test_cases, time_limit=1.0)
    assert r.final_result == "AC"
    assert r.total_score == 100
    assert len(r.cases) == 2
    assert r.cases[0].result == "AC"
    assert r.cases[1].result == "AC"
async def test_judge_partial_wa():
    test_cases = [
        {"case_id": "c1", "input": "1 2\n", "output": "3\n", "score": 50, "is_hidden": False},
        {"case_id": "c2", "input": "10 20\n", "output": "30\n", "score": 50, "is_hidden": True},
    ]
    r = await judge_submission(WRONG, test_cases, time_limit=1.0)
    assert r.final_result == "WA"
    assert r.total_score == 0
async def test_judge_one_ac_one_wa():
    code = "print(3)\n"
    test_cases = [
        {"case_id": "c1", "input": "1 2\n", "output": "3\n", "score": 50, "is_hidden": False},
        {"case_id": "c2", "input": "10 20\n", "output": "30\n", "score": 50, "is_hidden": True},
    ]
    r = await judge_submission(code, test_cases, time_limit=1.0)
    assert r.final_result == "WA"
    assert r.total_score == 50
async def test_judge_runtime_error():
    test_cases = [
        {"case_id": "c1", "input": "", "output": "", "score": 100, "is_hidden": False},
    ]
    r = await judge_submission(DIVZERO, test_cases, time_limit=1.0)
    assert r.final_result == "RE"
    assert r.total_score == 0
    assert r.cases[0].exit_code != 0