import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.auth import get_current_user
_VALID_BODY = {
    "id": "P1001",
    "title": "A+B Problem",
    "description": "Add two integers.",
    "input_description": "Two integers a and b.",
    "output_description": "The sum a+b.",
    "samples": [{"input": "1 2\n", "output": "3\n"}],
    "constraints": "|a|, |b| <= 10^9",
    "time_limit": 1.0,
    "memory_limit": 128,
    "difficulty": "easy",
    "tags": ["basic", "io"],
    "test_cases": [
        {"case_id": "c1", "input": "1 2\n", "output": "3\n", "score": 50, "is_hidden": False},
        {"case_id": "c2", "input": "-1 2\n", "output": "1\n", "score": 50, "is_hidden": True},
    ],
}
def _override_role(role: str):
    async def mock():
        return {
            "id": f"mock-{role}",
            "username": f"mock-{role}",
            "role": role,
            "is_active": True,
        }
    app.dependency_overrides[get_current_user] = mock
def _clear_override():
    app.dependency_overrides.pop(get_current_user, None)
def test_create_problem_201(api_client):
    _override_role("teacher")
    try:
        resp = api_client.post("/api/problems", json=_VALID_BODY)
        assert resp.status_code == 201
        body = resp.json()
        assert body["code"] == 201
        assert body["data"]["id"] == "P1001"
        assert len(body["data"]["test_cases"]) == 2
    finally:
        _clear_override()
def test_create_duplicate_409(api_client):
    _override_role("teacher")
    try:
        api_client.post("/api/problems", json=_VALID_BODY)
        resp = api_client.post("/api/problems", json=_VALID_BODY)
        assert resp.status_code == 409
        assert resp.json()["code"] == 409
    finally:
        _clear_override()
def test_create_score_not_100_422(api_client):
    _override_role("teacher")
    try:
        bad = dict(_VALID_BODY)
        bad = {**_VALID_BODY, "test_cases": [
            {"case_id": "c1", "input": "1\n", "output": "2\n", "score": 30, "is_hidden": False},
        ]}
        resp = api_client.post("/api/problems", json=bad)
        assert resp.status_code == 422
    finally:
        _clear_override()
def test_list_problems(api_client):
    _override_role("teacher")
    try:
        api_client.post("/api/problems", json=_VALID_BODY)
        api_client.post("/api/problems", json={**_VALID_BODY, "id": "P1002", "title": "Second"})
        resp = api_client.get("/api/problems?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert "test_cases" not in data["items"][0]
        assert "description" not in data["items"][0]
    finally:
        _clear_override()
def test_get_detail_as_teacher_includes_test_cases(api_client):
    _override_role("teacher")
    try:
        api_client.post("/api/problems", json=_VALID_BODY)
        resp = api_client.get("/api/problems/P1001")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == "P1001"
        assert len(data["test_cases"]) == 2
    finally:
        _clear_override()
def test_get_detail_as_student_excludes_test_cases(api_client):
    _override_role("teacher")
    try:
        api_client.post("/api/problems", json=_VALID_BODY)
    finally:
        _clear_override()
    _override_role("student")
    try:
        resp = api_client.get("/api/problems/P1001")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == "P1001"
        assert "test_cases" not in data
        assert len(data["samples"]) == 1
    finally:
        _clear_override()
def test_get_nonexistent_404(api_client):
    _override_role("teacher")
    try:
        resp = api_client.get("/api/problems/NOPE")
        assert resp.status_code == 404
        assert resp.json()["message"] == "problem not found"
    finally:
        _clear_override()
def test_update_problem(api_client):
    _override_role("teacher")
    try:
        api_client.post("/api/problems", json=_VALID_BODY)
        update_body = {**_VALID_BODY, "title": "Updated", "difficulty": "hard"}
        update_body.pop("id", None)
        resp = api_client.put("/api/problems/P1001", json=update_body)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Updated"
        assert data["difficulty"] == "hard"
        assert data["id"] == "P1001"
    finally:
        _clear_override()
def test_update_nonexistent_404(api_client):
    _override_role("teacher")
    try:
        update_body = {k: v for k, v in _VALID_BODY.items() if k != "id"}
        resp = api_client.put("/api/problems/NOPE", json=update_body)
        assert resp.status_code == 404
    finally:
        _clear_override()
def test_delete_problem(api_client):
    _override_role("teacher")
    try:
        api_client.post("/api/problems", json=_VALID_BODY)
        resp = api_client.delete("/api/problems/P1001")
        assert resp.status_code == 200
        resp = api_client.get("/api/problems/P1001")
        assert resp.status_code == 404
    finally:
        _clear_override()
def test_delete_nonexistent_404(api_client):
    _override_role("teacher")
    try:
        resp = api_client.delete("/api/problems/NOPE")
        assert resp.status_code == 404
    finally:
        _clear_override()
def test_student_cannot_create_403(api_client):
    _override_role("student")
    try:
        resp = api_client.post("/api/problems", json=_VALID_BODY)
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_student_cannot_delete_403(api_client):
    _override_role("teacher")
    try:
        api_client.post("/api/problems", json=_VALID_BODY)
    finally:
        _clear_override()
    _override_role("student")
    try:
        resp = api_client.delete("/api/problems/P1001")
        assert resp.status_code == 403
    finally:
        _clear_override()