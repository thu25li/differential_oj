from enum import Enum
from pydantic import BaseModel, Field
class SubmissionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
class SubmissionResult(str, Enum):
    AC = "AC"
    WA = "WA"
    RE = "RE"
    TLE = "TLE"
    SE = "SE"
class SubmissionCreate(BaseModel):
    problem_id: str
    language: str = Field(default="python")
    source_code: str = Field(min_length=1, max_length=64 * 1024)  # 64 KiB
