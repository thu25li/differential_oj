import re
from typing import Optional
_TEMP_PATH_PATTERN = re.compile(
    r"(?:[A-Za-z]:[\\/]|[\\/])(?:[^\s/\\]+[\\/])*[0-9a-fA-F]{32}[\\/]main\.py"
)
def sanitize_error_message(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return _TEMP_PATH_PATTERN.sub("<submission>/main.py", text)
def to_student_log_view(case_log: dict) -> dict:
    is_hidden = bool(case_log.get("is_hidden", False))
    view = {
        "case_id": case_log["case_id"],
        "result": case_log["result"],
        "score": case_log["score"],
        "time_used": case_log["time_used"],
        "message": case_log.get("message"),
        "is_hidden": is_hidden,
        "stderr": sanitize_error_message(case_log.get("stderr")),
    }
    if not is_hidden:
        view["stdout"] = case_log.get("stdout")
        view["expected_output"] = case_log.get("expected_output")
    return view
def to_teacher_log_view(case_log: dict) -> dict:
    return {
        "case_id": case_log["case_id"],
        "result": case_log["result"],
        "score": case_log["score"],
        "time_used": case_log["time_used"],
        "memory_used": case_log.get("memory_used"),
        "exit_code": case_log.get("exit_code"),
        "input_data": case_log.get("input_data"),
        "stdout": case_log.get("stdout"),
        "stderr": case_log.get("stderr"),
        "expected_output": case_log.get("expected_output"),
        "message": case_log.get("message"),
        "is_hidden": bool(case_log.get("is_hidden", False)),
    }