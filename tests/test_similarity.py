import pytest
from app.main import app
from app.services.similarity_service import (
    compute_similarity,
    normalize_code,
)
from app.utils.auth import get_current_user
SIMPLE_ADD_A = "a, b = map(int, input().split())\nprint(a + b)\n"
SIMPLE_ADD_B = "x, y = map(int, input().split())\nprint(x + y)\n"
DIFFERENT_CODE = "n = int(input())\nfactorial = 1\nfor i in range(1, n + 1):\n    factorial *= i\nprint(factorial)\n"
def test_normalize_handles_syntax_error():
    assert normalize_code("def f(:\n  pass") == ""
def test_identical_code_similarity_is_1():
    assert compute_similarity(SIMPLE_ADD_A, SIMPLE_ADD_A) == 1.0
def test_renamed_variables_still_similar():
    sim = compute_similarity(SIMPLE_ADD_A, SIMPLE_ADD_B)
    assert sim >= 0.95
def test_different_code_low_similarity():
    sim = compute_similarity(SIMPLE_ADD_A, DIFFERENT_CODE)
    assert sim < 0.5
def test_unparseable_code_returns_zero():
    assert compute_similarity("def f(:", SIMPLE_ADD_A) == 0.0
    assert compute_similarity(SIMPLE_ADD_A, "def f(:") == 0.0
def _override_role(role: str, user_id: str = None):
    async def mock():
        return {
            "id": user_id or f"mock-{role}-id",
            "username": f"mock-{role}",
            "role": role,
            "is_active": True,
        }
    app.dependency_overrides[get_current_user] = mock
def _clear_override():
    app.dependency_overrides.pop(get_current_user, None)
def _login_default_admin(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "admin12345"})
def _setup_problem(client):
    _login_default_admin(client)
    client.post("/api/problems", json={
        "id": "PSIM",
        "title": "Similar",
        "description": "d",
        "input_description": "i",
        "output_description": "o",
        "samples": [{"input": "1\n", "output": "2\n"}],
        "constraints": None,
        "time_limit": 1.0,
        "memory_limit": 128,
        "difficulty": "easy",
        "tags": [],
        "test_cases": [
            {"case_id": "c1", "input": "1\n", "output": "2\n", "score": 100, "is_hidden": False},
        ],
    })
    client.post("/api/auth/logout")
def _submit_as(client, uid, source):
    _override_role("student", user_id=uid)
    try:
        resp = client.post("/api/submissions", json={
            "problem_id": "PSIM",
            "language": "python",
            "source_code": source,
        })
        import time
        sub_id = resp.json()["data"]["submission_id"]
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            r = client.get(f"/api/submissions/{sub_id}")
            if r.json()["data"]["status"] in ("finished", "failed"):
                break
            time.sleep(0.1)
    finally:
        _clear_override()
    return sub_id
def test_similarity_check_finds_duplicate(api_client):
    _setup_problem(api_client)
    _submit_as(api_client, "s1", SIMPLE_ADD_A)
    _submit_as(api_client, "s2", SIMPLE_ADD_B)
    _override_role("teacher")
    try:
        resp = api_client.post("/api/problems/PSIM/similarity-check")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["report_count"] >= 1
        resp = api_client.get("/api/problems/PSIM/similarity-reports")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1
        assert all(r["similarity"] >= 0.7 for r in items)
        assert all(r["method"] == "ast" for r in items)
    finally:
        _clear_override()
def test_similarity_check_excludes_below_threshold(api_client):
    _setup_problem(api_client)
    _submit_as(api_client, "s1", SIMPLE_ADD_A)
    _submit_as(api_client, "s2", DIFFERENT_CODE)
    _override_role("teacher")
    try:
        resp = api_client.post("/api/problems/PSIM/similarity-check")
        assert resp.status_code == 200
        assert resp.json()["data"]["report_count"] == 0
    finally:
        _clear_override()
def test_similarity_check_replaces_previous_reports(api_client):
    _setup_problem(api_client)
    _submit_as(api_client, "s1", SIMPLE_ADD_A)
    _override_role("teacher")
    try:
        api_client.post("/api/problems/PSIM/similarity-check")
        items = api_client.get("/api/problems/PSIM/similarity-reports").json()["data"]["items"]
        assert len(items) == 0
    finally:
        _clear_override()
    _submit_as(api_client, "s2", SIMPLE_ADD_B)
    _override_role("teacher")
    try:
        api_client.post("/api/problems/PSIM/similarity-check")
        items = api_client.get("/api/problems/PSIM/similarity-reports").json()["data"]["items"]
        assert len(items) == 1
    finally:
        _clear_override()
def test_similarity_check_nonexistent_problem_404(api_client):
    _override_role("teacher")
    try:
        resp = api_client.post("/api/problems/NOPE/similarity-check")
        assert resp.status_code == 404
    finally:
        _clear_override()
def test_similarity_check_student_forbidden_403(api_client):
    _override_role("student", user_id="s1")
    try:
        resp = api_client.post("/api/problems/PSIM/similarity-check")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_similarity_reports_student_forbidden_403(api_client):
    _override_role("student", user_id="s1")
    try:
        resp = api_client.get("/api/problems/PSIM/similarity-reports")
        assert resp.status_code == 403
    finally:
        _clear_override()
