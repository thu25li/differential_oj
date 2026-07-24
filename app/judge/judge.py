from dataclasses import dataclass, field
from typing import List
from app.judge.runner import (
    CaseResult,
    cleanup_submission_dir,
    create_submission_dir,
    run_single_case,
)
@dataclass
class JudgeResult:
    final_result: str
    total_score: int
    total_time: float
    cases: List[CaseResult]
async def judge_submission(
    source_code: str,
    test_cases: List[dict],
    time_limit: float,
) -> JudgeResult:
    temp_dir = create_submission_dir(source_code)
    code_path = temp_dir / "main.py"
    try:
        case_results: List[CaseResult] = []
        for tc in test_cases:
            result = await run_single_case(
                code_path=code_path,
                case_id=tc["case_id"],
                stdin_data=tc["input"],
                expected_output=tc["output"],
                score=tc["score"],
                is_hidden=tc["is_hidden"],
                time_limit=time_limit,
            )
            case_results.append(result)
            if result.result == "TLE":
                break
        return _aggregate(case_results)
    finally:
        cleanup_submission_dir(temp_dir)
def _aggregate(case_results: List[CaseResult]) -> JudgeResult:
    if not case_results:
        return JudgeResult(
            final_result="SE",
            total_score=0,
            total_time=0.0,
            cases=[],
        )
    if all(cr.result == "AC" for cr in case_results):
        final_result = "AC"
    elif any(cr.result == "SE" for cr in case_results):
        final_result = "SE"
    elif any(cr.result == "TLE" for cr in case_results):
        final_result = "TLE"
    elif any(cr.result == "RE" for cr in case_results):
        final_result = "RE"
    else:
        final_result = "WA"
    total_score = sum(cr.score for cr in case_results if cr.result == "AC")
    total_time = round(sum(cr.time_used for cr in case_results), 6)
    return JudgeResult(
        final_result=final_result,
        total_score=total_score,
        total_time=total_time,
        cases=case_results,
    )