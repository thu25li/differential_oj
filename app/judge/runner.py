import asyncio
import shutil
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from app.judge.comparator import compare_output
@dataclass
class CaseResult:
    case_id: str
    result: str
    score: int
    time_used: float
    exit_code: Optional[int]
    stdout: str
    stderr: str
    is_hidden: bool
    message: str = ""
    input_data: str = ""
    expected_output: str = ""
def create_submission_dir(source_code: str) -> Path:
    submission_uuid = uuid.uuid4().hex
    temp_dir = Path(tempfile.gettempdir()) / "oj_submissions" / submission_uuid
    temp_dir.mkdir(parents=True, exist_ok=True)
    (temp_dir / "main.py").write_text(source_code, encoding="utf-8")
    return temp_dir
def cleanup_submission_dir(temp_dir: Path) -> None:
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    except Exception:
        pass
async def run_single_case(
    code_path: Path,
    case_id: str,
    stdin_data: str,
    expected_output: str,
    score: int,
    is_hidden: bool,
    time_limit: float,
) -> CaseResult:
    start = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(code_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except Exception as e:
        return CaseResult(
            case_id=case_id, result="SE", score=0, time_used=0.0,
            exit_code=None, stdout="", stderr=str(e),
            is_hidden=is_hidden, message="failed to spawn subprocess",
            input_data=stdin_data, expected_output=expected_output,
        )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(input=stdin_data.encode("utf-8")),
            timeout=time_limit,
        )
    except asyncio.TimeoutError:
        await _kill_proc(proc)
        return CaseResult(
            case_id=case_id, result="TLE", score=0, time_used=time_limit,
            exit_code=None, stdout="", stderr="",
            is_hidden=is_hidden, message=f"time limit exceeded ({time_limit}s)",
            input_data=stdin_data, expected_output=expected_output,
        )
    except Exception as e:
        await _kill_proc(proc)
        return CaseResult(
            case_id=case_id, result="SE", score=0, time_used=0.0,
            exit_code=None, stdout="", stderr=str(e),
            is_hidden=is_hidden, message="subprocess communication error",
            input_data=stdin_data, expected_output=expected_output,
        )
    elapsed = time.monotonic() - start
    exit_code = proc.returncode
    try:
        stdout = stdout_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            stderr = stderr_bytes.decode("utf-8", errors="replace")
        except Exception:
            stderr = ""
        return CaseResult(
            case_id=case_id, result="RE", score=0, time_used=elapsed,
            exit_code=exit_code, stdout="", stderr=stderr,
            is_hidden=is_hidden, message="program output is not valid UTF-8",
            input_data=stdin_data, expected_output=expected_output,
        )
    try:
        stderr = stderr_bytes.decode("utf-8")
    except UnicodeDecodeError:
        stderr = "<stderr is not valid UTF-8>"
    if exit_code != 0:
        return CaseResult(
            case_id=case_id, result="RE", score=0, time_used=elapsed,
            exit_code=exit_code, stdout=stdout, stderr=stderr,
            is_hidden=is_hidden, message=f"non-zero exit code: {exit_code}",
            input_data=stdin_data, expected_output=expected_output,
        )
    if compare_output(stdout, expected_output):
        return CaseResult(
            case_id=case_id, result="AC", score=score, time_used=elapsed,
            exit_code=exit_code, stdout=stdout, stderr=stderr,
            is_hidden=is_hidden, message="accepted",
            input_data=stdin_data, expected_output=expected_output,
        )
    return CaseResult(
        case_id=case_id, result="WA", score=0, time_used=elapsed,
        exit_code=exit_code, stdout=stdout, stderr=stderr,
        is_hidden=is_hidden, message="wrong answer",
        input_data=stdin_data, expected_output=expected_output,
    )
async def _kill_proc(proc: asyncio.subprocess.Process) -> None:
    try:
        proc.kill()
        await proc.wait()
    except ProcessLookupError:
        pass
    except Exception:
        pass
