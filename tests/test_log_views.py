from app.utils.log_views import (
    sanitize_error_message,
    to_student_log_view,
    to_teacher_log_view,
)
def test_sanitize_linux_path():
    stderr = 'Traceback:\n  File "/tmp/oj_submissions/1234567890abcdef1234567890abcdef/main.py", line 3\n    print(1/0)\nZeroDivisionError'
    out = sanitize_error_message(stderr)
    assert "/tmp/oj_submissions/" not in out
    assert "<submission>/main.py" in out
def test_sanitize_windows_path():
    stderr = r'  File "C:\Users\me\Temp\oj_submissions\abcdef0123456789abcdef0123456789\main.py", line 5'
    out = sanitize_error_message(stderr)
    assert r"C:\Users" not in out
    assert "<submission>/main.py" in out
def test_sanitize_already_sanitized_idempotent():
    text = "error at <submission>/main.py line 3"
    assert sanitize_error_message(text) == text
def test_sanitize_none_returns_none():
    assert sanitize_error_message(None) is None
def test_sanitize_no_path_unchanged():
    text = "program output is not valid UTF-8"
    assert sanitize_error_message(text) == text
_PUBLIC_CASE = {
    "case_id": "c1",
    "result": "AC",
    "score": 50,
    "time_used": 0.05,
    "memory_used": None,
    "exit_code": 0,
    "input_data": "1 2\n",
    "stdout": "3\n",
    "stderr": "",
    "expected_output": "3\n",
    "message": "accepted",
    "is_hidden": False,
}
_HIDDEN_CASE = {
    "case_id": "c2",
    "result": "WA",
    "score": 0,
    "time_used": 0.08,
    "memory_used": None,
    "exit_code": 0,
    "input_data": "secret input\n",
    "stdout": "wrong output\n",
    "stderr": "",
    "expected_output": "secret expected\n",
    "message": "wrong answer",
    "is_hidden": True,
}
def test_student_view_public_case_includes_stdout_and_expected():
    view = to_student_log_view(_PUBLIC_CASE)
    assert view["case_id"] == "c1"
    assert view["result"] == "AC"
    assert view["score"] == 50
    assert view["stdout"] == "3\n"
    assert view["expected_output"] == "3\n"
    assert view["is_hidden"] is False
def test_student_view_hidden_case_excludes_sensitive_fields():
    view = to_student_log_view(_HIDDEN_CASE)
    assert view["case_id"] == "c2"
    assert view["result"] == "WA"
    assert view["is_hidden"] is True
    assert "input_data" not in view
    assert "stdout" not in view
    assert "expected_output" not in view
    assert view["message"] == "wrong answer"
    assert view["time_used"] == 0.08
def test_student_view_sanitizes_stderr():
    case = dict(_PUBLIC_CASE)
    case["stderr"] = 'File "/tmp/oj_submissions/abcdef0123456789abcdef0123456789/main.py", line 3'
    view = to_student_log_view(case)
    assert "/tmp/oj_submissions/" not in view["stderr"]
    assert "<submission>/main.py" in view["stderr"]
def test_student_view_never_exposes_input_data():
    view = to_student_log_view(_PUBLIC_CASE)
    assert "input_data" not in view
def test_teacher_view_includes_all_fields():
    view = to_teacher_log_view(_HIDDEN_CASE)
    assert view["case_id"] == "c2"
    assert view["is_hidden"] is True
    assert view["input_data"] == "secret input\n"
    assert view["stdout"] == "wrong output\n"
    assert view["expected_output"] == "secret expected\n"
    assert view["stderr"] == ""
    assert view["exit_code"] == 0
    assert view["memory_used"] is None
def test_teacher_view_does_not_sanitize_stderr():
    case = dict(_PUBLIC_CASE)
    case["stderr"] = 'File "/tmp/oj_submissions/abcdef0123456789abcdef0123456789/main.py", line 3'
    view = to_teacher_log_view(case)
    assert "/tmp/oj_submissions/" in view["stderr"]