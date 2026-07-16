import time
import pytest
from app.main import app
from app.utils.auth import get_current_user
_VALID_PROBLEM = {
    "id": "P1001",
    "title": "A+B",
    "description": "add",
    "input_description": "a b",
    "output_description": "a+b",
    "samples": [{"input": "1 2\n", "output": "3\n"}],
    "constraints": None,
    "time_limit": 1.0,
    "memory_limit": 128,
    "difficulty": "easy",
    "tags": [],
    "test_cases": [
        {"case_id": "c1", "input": "1 2\n", "output": "3\n", "score": 50, "is_hidden": False},
        {"case_id": "c2", "input": "10 20\n", "output": "30\n", "score": 50, "is_hidden": True},
    ],
}
def _login_default_admin(client):
    client.post("/api/auth/login", json={"username": "admin", "password": "admin12345"})
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
def _setup_problem_and_submit(client, source_code=None, user_id="s1"):
    if source_code is None:
        source_code = "a, b = map(int, input().split())\nprint(a + b)\n"
    _login_default_admin(client)
    client.post("/api/problems", json=_VALID_PROBLEM)
    client.post("/api/auth/logout")
    _override_role("student", user_id=user_id)
    try:
        resp = client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": source_code,
        })
        sub_id = resp.json()["data"]["submission_id"]
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            r = client.get(f"/api/submissions/{sub_id}")
            if r.json()["data"]["status"] in ("finished", "failed"):
                break
            time.sleep(0.1)
        return sub_id
    finally:
        _clear_override()
def test_student_views_own_logs_uses_student_view(api_client):
    sub_id = _setup_problem_and_submit(api_client)
    _override_role("student", user_id="s1")
    try:
        resp = api_client.get(f"/api/submissions/{sub_id}/logs")
        assert resp.status_code == 200
        cases = resp.json()["data"]["cases"]
        assert len(cases) == 2
        for c in cases:
            assert "input_data" not in c
            assert "case_id" in c
            assert "result" in c
            assert "score" in c
            assert "time_used" in c
            assert "message" in c
            assert "stderr" in c
            assert "is_hidden" in c
    finally:
        _clear_override()
def test_student_view_hidden_case_excludes_stdout_and_expected(api_client):
    sub_id = _setup_problem_and_submit(api_client)
    _override_role("student", user_id="s1")
    try:
        resp = api_client.get(f"/api/submissions/{sub_id}/logs")
        cases = resp.json()["data"]["cases"]
        hidden = [c for c in cases if c["is_hidden"]][0]
        assert "stdout" not in hidden
        assert "expected_output" not in hidden
        public = [c for c in cases if not c["is_hidden"]][0]
        assert "stdout" in public
        assert "expected_output" in public
    finally:
        _clear_override()
def test_student_cannot_view_others_logs_403(api_client):
    sub_id = _setup_problem_and_submit(api_client, user_id="s1")
    _override_role("student", user_id="s2")
    try:
        resp = api_client.get(f"/api/submissions/{sub_id}/logs")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_teacher_views_full_logs_includes_all_fields(api_client):
    sub_id = _setup_problem_and_submit(api_client)
    _override_role("teacher")
    try:
        resp = api_client.get(f"/api/submissions/{sub_id}/logs")
        assert resp.status_code == 200
        cases = resp.json()["data"]["cases"]
        for c in cases:
            assert "input_data" in c
            assert "stdout" in c
            assert "expected_output" in c
            assert "exit_code" in c
    finally:
        _clear_override()
def test_teacher_viewing_full_logs_writes_audit(api_client):
    sub_id = _setup_problem_and_submit(api_client)
    _override_role("teacher")
    try:
        api_client.get(f"/api/submissions/{sub_id}/logs")
    finally:
        _clear_override()
    _override_role("admin")
    try:
        resp = api_client.get("/api/audit-logs?action=VIEW_FULL_JUDGE_LOG")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert any(item["target_id"] == sub_id for item in items)
    finally:
        _clear_override()
def test_get_logs_nonexistent_submission_404(api_client):
    _override_role("teacher")
    try:
        resp = api_client.get("/api/submissions/nope/logs")
        assert resp.status_code == 404
    finally:
        _clear_override()
def test_logs_endpoint_requires_teacher_or_admin(api_client):
    _override_role("student")
    try:
        resp = api_client.get("/api/logs")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_logs_endpoint_returns_full_view(api_client):
    _setup_problem_and_submit(api_client)
    _override_role("teacher")
    try:
        resp = api_client.get("/api/logs")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 2
        for item in items:
            assert "input_data" in item
            assert "stdout" in item
    finally:
        _clear_override()
def test_logs_endpoint_filter_by_result(api_client):
    _setup_problem_and_submit(api_client, source_code="print(0)\n")
    _override_role("teacher")
    try:
        resp = api_client.get("/api/logs?result=WA")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) > 0
        for item in items:
            assert item["result"] == "WA"
    finally:
        _clear_override()
def test_logs_endpoint_filter_by_submission(api_client):
    sub_id = _setup_problem_and_submit(api_client)
    _override_role("teacher")
    try:
        resp = api_client.get(f"/api/logs?submission_id={sub_id}")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) == 2
        for item in items:
            assert item["submission_id"] == sub_id
    finally:
        _clear_override()
def test_audit_logs_requires_admin(api_client):
    _override_role("teacher")
    try:
        resp = api_client.get("/api/audit-logs")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_audit_logs_returns_actions(api_client):
    sub_id = _setup_problem_and_submit(api_client)
    _override_role("teacher")
    try:
        api_client.get(f"/api/submissions/{sub_id}/logs")
    finally:
        _clear_override()
    _override_role("admin")
    try:
        resp = api_client.get("/api/audit-logs")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) > 0
    finally:
        _clear_override()
def test_audit_logs_filter_by_action(api_client):
    sub_id = _setup_problem_and_submit(api_client)
    _override_role("teacher")
    try:
        api_client.get(f"/api/submissions/{sub_id}/logs")
    finally:
        _clear_override()
    _override_role("admin")
    try:
        resp = api_client.get("/api/audit-logs?action=VIEW_FULL_JUDGE_LOG")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        for item in items:
            assert item["action"] == "VIEW_FULL_JUDGE_LOG"
    finally:
        _clear_override()
def test_audit_logs_reflects_user_role_change(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/auth/register", json={
        "username": "promotee",
        "password": "password123",
    })
    resp = api_client.get("/api/users")
    target = next(u for u in resp.json()["data"]["items"] if u["username"] == "promotee")
    api_client.put(f"/api/users/{target['id']}", json={"role": "teacher"})
    resp = api_client.get("/api/audit-logs?action=UPDATE_USER_ROLE")
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert any(item["target_id"] == target["id"] for item in items)
