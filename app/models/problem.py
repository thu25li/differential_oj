import re
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
class Sample(BaseModel):
    input: str
    output: str
class TestCaseCreate(BaseModel):
    __test__=False
    case_id: str = Field(min_length=1, max_length=32)
    input: str
    output: str
    score: int = Field(ge=0)
    is_hidden: bool
    @field_validator("case_id")
    @classmethod
    def validate_case_id(cls, v: str) -> str:
        if not ID_PATTERN.match(v):
            raise ValueError("case_id may only contain letters, digits, underscore or hyphen")
        return v
class TestCaseResponse(BaseModel):
    case_id: str
    input: str
    output: str
    score: int
    is_hidden: bool
def _validate_scores_and_uniqueness(test_cases: List[TestCaseCreate]) -> None:
    total = sum(tc.score for tc in test_cases)
    if total != 100:
        raise ValueError(f"sum of test case scores must be 100, got {total}")
    case_ids = [tc.case_id for tc in test_cases]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("duplicate case_id within the same problem")
class ProblemCreate(BaseModel):
    id: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=100)
    description: str
    input_description: str
    output_description: str
    samples: List[Sample] = Field(min_length=1)
    constraints: Optional[str] = None
    time_limit: float = Field(gt=0, description="秒")
    memory_limit: int = Field(gt=0, description="MB")
    difficulty: Difficulty
    tags: List[str] = Field(default_factory=list)
    test_cases: List[TestCaseCreate] = Field(min_length=1)
    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not ID_PATTERN.match(v):
            raise ValueError("id may only contain letters, digits, underscore or hyphen")
        return v
    @model_validator(mode="after")
    def _check(self) -> "ProblemCreate":
        _validate_scores_and_uniqueness(self.test_cases)
        return self
class ProblemUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str
    input_description: str
    output_description: str
    samples: List[Sample] = Field(min_length=1)
    constraints: Optional[str] = None
    time_limit: float = Field(gt=0)
    memory_limit: int = Field(gt=0)
    difficulty: Difficulty
    tags: List[str] = Field(default_factory=list)
    test_cases: List[TestCaseCreate] = Field(min_length=1)
    @model_validator(mode="after")
    def _check(self) -> "ProblemUpdate":
        _validate_scores_and_uniqueness(self.test_cases)
        return self
class ProblemBrief(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    tags: List[str]
    time_limit: float
    memory_limit: int
class ProblemPublic(BaseModel):
    id: str
    title: str
    description: str
    input_description: str
    output_description: str
    samples: List[Sample]
    constraints: Optional[str]
    time_limit: float
    memory_limit: int
    difficulty: Difficulty
    tags: List[str]
class ProblemFull(ProblemPublic):
    test_cases: List[TestCaseResponse]