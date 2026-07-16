import pytest
from pydantic import ValidationError
from app.models.problem import (
    Difficulty,
    ProblemCreate,
    Sample,
    TestCaseCreate,
)


def _valid_kwargs(**overrides):
    """构造一份合法的 ProblemCreate 参数，测试时按需覆盖某字段。"""
    base = dict(
        id="P1001",
        title="A+B Problem",
        description="Add two integers.",
        input_description="Two integers a and b.",
        output_description="The sum a+b.",
        samples=[Sample(input="1 2\n", output="3\n")],
        constraints="|a|, |b| <= 10^9",
        time_limit=1.0,
        memory_limit=128,
        difficulty=Difficulty.EASY,
        tags=["basic", "io"],
        test_cases=[
            TestCaseCreate(case_id="case_01", input="1 2\n", output="3\n", score=50, is_hidden=False),
            TestCaseCreate(case_id="case_02", input="-1 2\n", output="1\n", score=50, is_hidden=True),
        ],
    )
    base.update(overrides)
    return base
def test_valid_problem_create():
    p = ProblemCreate(**_valid_kwargs())
    assert p.id == "P1001"
    assert len(p.test_cases) == 2
    assert p.test_cases[0].score == 50


def test_id_too_long():
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(id="P" + "0" * 32))  # 33 chars
def test_id_invalid_chars():
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(id="P 1001"))  # space not allowed
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(id="P1001!"))  # ! not allowed
def test_title_too_long():
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(title="x" * 101))
def test_score_sum_not_100():
    bad_cases = [
        TestCaseCreate(case_id="c1", input="", output="", score=30, is_hidden=False),
        TestCaseCreate(case_id="c2", input="", output="", score=40, is_hidden=False),
    ]
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(test_cases=bad_cases))
def test_duplicate_case_id():
    bad_cases = [
        TestCaseCreate(case_id="dup", input="", output="", score=50, is_hidden=False),
        TestCaseCreate(case_id="dup", input="", output="", score=50, is_hidden=False),
    ]
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(test_cases=bad_cases))
def test_empty_test_cases():
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(test_cases=[]))
def test_empty_samples():
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(samples=[]))
def test_time_limit_must_be_positive():
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(time_limit=0))
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(time_limit=-1))
def test_memory_limit_must_be_positive():
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(memory_limit=0))
def test_difficulty_enum():
    with pytest.raises(ValidationError):
        ProblemCreate(**_valid_kwargs(difficulty="impossible"))