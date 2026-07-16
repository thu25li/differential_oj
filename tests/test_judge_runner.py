import pytest
from app.judge.runner import (
    cleanup_submission_dir,
    create_submission_dir,
    run_single_case,
)
SIMPLE_ADD = "a, b = map(int, input().split())\nprint(a + b)\n"
WRONG_ANSWER = "print(0)\n"
RUNTIME_ERROR = "print(1 / 0)\n"
INFINITE_LOOP = "while True:\n    pass\n"
NON_UTF8_OUTPUT = "import sys\nsys.stdout.buffer.write(b'\\xff\\xfe\\x00\\x01')\n"
async def test_run_ac():
    path = create_submission_dir(SIMPLE_ADD)
    try:
        result = await run_single_case(
            code_path=path / "main.py",
            case_id="c1",
            stdin_data="1 2\n",
            expected_output="3\n",
            score=50,
            is_hidden=False,
            time_limit=1.0,
        )
        assert result.result == "AC"
        assert result.score == 50
        assert result.exit_code == 0
        assert result.time_used < 1.0
    finally:
        cleanup_submission_dir(path)
async def test_run_wa():
    path = create_submission_dir(WRONG_ANSWER)
    try:
        result = await run_single_case(
            code_path=path / "main.py",
            case_id="c1",
            stdin_data="1 2\n",
            expected_output="3\n",
            score=50,
            is_hidden=False,
            time_limit=1.0,
        )
        assert result.result == "WA"
        assert result.score == 0
        assert result.exit_code == 0
    finally:
        cleanup_submission_dir(path)
async def test_run_re_divzero():
    path = create_submission_dir(RUNTIME_ERROR)
    try:
        result = await run_single_case(
            code_path=path / "main.py",
            case_id="c1",
            stdin_data="",
            expected_output="",
            score=50,
            is_hidden=False,
            time_limit=1.0,
        )
        assert result.result == "RE"
        assert result.exit_code != 0
        assert result.score == 0
    finally:
        cleanup_submission_dir(path)
async def test_run_tle():
    path = create_submission_dir(INFINITE_LOOP)
    try:
        result = await run_single_case(
            code_path=path / "main.py",
            case_id="c1",
            stdin_data="",
            expected_output="",
            score=50,
            is_hidden=False,
            time_limit=0.5,
        )
        assert result.result == "TLE"
        assert result.score == 0
        assert result.exit_code is None
    finally:
        cleanup_submission_dir(path)
async def test_non_utf8_output_treated_as_re():
    path = create_submission_dir(NON_UTF8_OUTPUT)
    try:
        result = await run_single_case(
            code_path=path / "main.py",
            case_id="c1",
            stdin_data="",
            expected_output="",
            score=50,
            is_hidden=False,
            time_limit=1.0,
        )
        assert result.result == "RE"
        assert "UTF-8" in result.message or "utf" in result.message.lower()
    finally:
        cleanup_submission_dir(path)
async def test_hidden_flag_passed_through():
    path = create_submission_dir(SIMPLE_ADD)
    try:
        result = await run_single_case(
            code_path=path / "main.py",
            case_id="c_hidden",
            stdin_data="10 20\n",
            expected_output="30\n",
            score=100,
            is_hidden=True,
            time_limit=1.0,
        )
        assert result.is_hidden is True
        assert result.result == "AC"
    finally:
        cleanup_submission_dir(path)
def test_temp_dir_created_and_cleaned():
    path = create_submission_dir(SIMPLE_ADD)
    assert path.exists()
    assert (path / "main.py").exists()
    assert (path / "main.py").read_text(encoding="utf-8") == SIMPLE_ADD
    cleanup_submission_dir(path)
    assert not path.exists()
def test_cleanup_idempotent():
    path = create_submission_dir(SIMPLE_ADD)
    cleanup_submission_dir(path)
    cleanup_submission_dir(path)
    assert not path.exists()