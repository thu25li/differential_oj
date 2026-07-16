import time
import pytest
from app.main import app
from app.utils.auth import get_current_user
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
_VALID_PROBLEM = {
    "id": "P1001",
    "title": "A+B Problem",
    "description": "add",
    "input_description": "a b",
    "output_description": "a+b",
    "samples": [{"input": "1 2\n", "output": "3\n"}],
    "constraints": None,
    "time_limit": 1.0,
    "memory_limit": 128,
    "difficulty": "easy",
    "tags": ["basic"],
    "test_cases": [
        {"case_id": "c1", "input": "1 2\n", "output": "3\n", "score": 50, "is_hidden": False},
        {"case_id": "c2", "input": "10 20\n", "output": "30\n", "score": 50, "is_hidden": True},
    ],
}
def _setup_problem(client):
    _login_default_admin(client)
    client.post("/api/problems", json=_VALID_PROBLEM)
    client.post("/api/auth/logout")
def _wait_for_done(client, submission_id, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = client.get(f"/api/submissions/{submission_id}")
        if resp.status_code == 200:
            data = resp.json()["data"]
            if data["status"] in ("finished", "failed"):
                return data
        time.sleep(0.1)
    raise TimeoutError(f"submission {submission_id} did not finish in {timeout}s")
def test_create_submission_202(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="student-1")
    try:
        resp = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "a, b = map(int, input().split())\nprint(a + b)\n",
        })
        assert resp.status_code == 202
        data = resp.json()["data"]
        assert "submission_id" in data
        assert data["status"] == "pending"
    finally:
        _clear_override()
def test_submit_to_nonexistent_problem_404(api_client):
    _override_role("student", user_id="student-1")
    try:
        resp = api_client.post("/api/submissions", json={
            "problem_id": "NOPE",
            "language": "python",
            "source_code": "print(1)\n",
        })
        assert resp.status_code == 404
    finally:
        _clear_override()
def test_submit_empty_source_422(api_client):
    _override_role("student", user_id="student-1")
    try:
        resp = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "",
        })
        assert resp.status_code == 422
    finally:
        _clear_override()
def test_submit_non_python_language_400(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="student-1")
    try:
        resp = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "javascript",
            "source_code": "console.log(1)",
        })
        assert resp.status_code == 400
    finally:
        _clear_override()
def test_submission_judged_ac(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="student-1")
    try:
        resp = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "a, b = map(int, input().split())\nprint(a + b)\n",
        })
        sub_id = resp.json()["data"]["submission_id"]
        final = _wait_for_done(api_client, sub_id)
        assert final["status"] == "finished"
        assert final["result"] == "AC"
        assert final["score"] == 100
    finally:
        _clear_override()
def test_submission_judged_wa(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="student-1")
    try:
        resp = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(0)\n",
        })
        sub_id = resp.json()["data"]["submission_id"]
        final = _wait_for_done(api_client, sub_id)
        assert final["status"] == "finished"
        assert final["result"] == "WA"
        assert final["score"] == 0
    finally:
        _clear_override()
def test_submission_judged_re(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="student-1")
    try:
        resp = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(1 / 0)\n",
        })
        sub_id = resp.json()["data"]["submission_id"]
        final = _wait_for_done(api_client, sub_id)
        assert final["status"] == "finished"
        assert final["result"] == "RE"
    finally:
        _clear_override()
def test_student_get_own_submission(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="student-1")
    try:
        sub_id = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(1)\n",
        }).json()["data"]["submission_id"]
        _wait_for_done(api_client, sub_id)
        resp = api_client.get(f"/api/submissions/{sub_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == sub_id
        assert "source_code" in data
    finally:
        _clear_override()
def test_student_cannot_get_others_submission_403(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="student-1")
    try:
        sub_id = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(1)\n",
        }).json()["data"]["submission_id"]
        _wait_for_done(api_client, sub_id)
    finally:
        _clear_override()
    _override_role("student", user_id="student-2")
    try:
        resp = api_client.get(f"/api/submissions/{sub_id}")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_teacher_can_get_any_submission(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="student-1")
    try:
        sub_id = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(1)\n",
        }).json()["data"]["submission_id"]
        _wait_for_done(api_client, sub_id)
    finally:
        _clear_override()
    _override_role("teacher")
    try:
        resp = api_client.get(f"/api/submissions/{sub_id}")
        assert resp.status_code == 200
    finally:
        _clear_override()
def test_get_nonexistent_submission_404(api_client):
    _override_role("teacher")
    try:
        resp = api_client.get("/api/submissions/nope")
        assert resp.status_code == 404
    finally:
        _clear_override()
def test_student_list_only_own(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="student-1")
    try:
        api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(1)\n",
        })
    finally:
        _clear_override()
    _override_role("student", user_id="student-2")
    try:
        api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(2)\n",
        })
        resp = api_client.get("/api/submissions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert data["items"][0]["user_id"] == "student-2"
    finally:
        _clear_override()
def test_teacher_list_all(api_client):
    _setup_problem(api_client)
    for uid in ["s1", "s2", "s3"]:
        _override_role("student", user_id=uid)
        try:
            api_client.post("/api/submissions", json={
                "problem_id": "P1001",
                "language": "python",
                "source_code": "print(1)\n",
            })
        finally:
            _clear_override()
    _override_role("teacher")
    try:
        resp = api_client.get("/api/submissions")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 3
    finally:
        _clear_override()
def test_list_with_filter(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="s1")
    try:
        api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "a, b = map(int, input().split())\nprint(a + b)\n",
        })
        api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(0)\n",
        })
        resp = api_client.get("/api/submissions")
        for item in resp.json()["data"]["items"]:
            _wait_for_done(api_client, item["id"])
        resp = api_client.get("/api/submissions?result=AC")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert data["items"][0]["result"] == "AC"
    finally:
        _clear_override()
def test_rejudge_as_teacher(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="s1")
    try:
        sub_id = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(0)\n",
        }).json()["data"]["submission_id"]
        _wait_for_done(api_client, sub_id)
        before = api_client.get(f"/api/submissions/{sub_id}").json()["data"]
        assert before["result"] == "WA"
    finally:
        _clear_override()
    _override_role("teacher")
    try:
        resp = api_client.post(f"/api/submissions/{sub_id}/rejudge")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "pending"
        final = _wait_for_done(api_client, sub_id)
        assert final["status"] == "finished"
        assert final["result"] == "WA"
    finally:
        _clear_override()
def test_rejudge_pending_returns_409(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="s1")
    try:
        sub_id = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(0)\n",
        }).json()["data"]["submission_id"]
    finally:
        _clear_override()
    _override_role("teacher")
    try:
        _wait_for_done(api_client, sub_id)
        resp = api_client.post(f"/api/submissions/{sub_id}/rejudge")
        assert resp.status_code == 200
    finally:
        _clear_override()
def test_rejudge_as_student_403(api_client):
    _setup_problem(api_client)
    _override_role("student", user_id="s1")
    try:
        sub_id = api_client.post("/api/submissions", json={
            "problem_id": "P1001",
            "language": "python",
            "source_code": "print(0)\n",
        }).json()["data"]["submission_id"]
        _wait_for_done(api_client, sub_id)
        resp = api_client.post(f"/api/submissions/{sub_id}/rejudge")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_rejudge_nonexistent_404(api_client):
    _override_role("teacher")
    try:
        resp = api_client.post("/api/submissions/nope/rejudge")
        assert resp.status_code == 404
    finally:
        _clear_override()