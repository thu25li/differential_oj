import pytest
from app.main import app
from app.utils.auth import get_current_user
def _login_default_admin(client):
    client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin12345",
    })
def _override_role(role: str):
    async def mock():
        return {
            "id": f"mock-{role}-id",
            "username": f"mock-{role}",
            "role": role,
            "is_active": True,
        }
    app.dependency_overrides[get_current_user] = mock
def _clear_override():
    app.dependency_overrides.pop(get_current_user, None)
def test_admin_can_list_users(api_client):
    _login_default_admin(api_client)
    resp = api_client.get("/api/users")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 1
    for item in data["items"]:
        assert "password_hash" not in item
def test_teacher_cannot_list_users_403(api_client):
    _override_role("teacher")
    try:
        resp = api_client.get("/api/users")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_student_cannot_list_users_403(api_client):
    _override_role("student")
    try:
        resp = api_client.get("/api/users")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_unauthenticated_cannot_list_users_401(api_client):
    resp = api_client.get("/api/users")
    assert resp.status_code == 401
def test_admin_can_get_user_detail(api_client):
    _login_default_admin(api_client)
    me = api_client.get("/api/auth/me").json()["data"]
    resp = api_client.get(f"/api/users/{me['id']}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == me["id"]
    assert "password_hash" not in resp.json()["data"]
def test_get_nonexistent_user_404(api_client):
    _login_default_admin(api_client)
    resp = api_client.get("/api/users/nonexistent-id")
    assert resp.status_code == 404
def test_admin_can_promote_user(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/auth/register", json={
        "username": "topromote",
        "password": "password123",
    })
    resp = api_client.get("/api/users")
    target = next(
        u for u in resp.json()["data"]["items"] if u["username"] == "topromote"
    )
    resp = api_client.put(f"/api/users/{target['id']}", json={"role": "teacher"})
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "teacher"
def test_admin_can_disable_then_enable_user(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/auth/register", json={
        "username": "toggleuser",
        "password": "password123",
    })
    resp = api_client.get("/api/users")
    target = next(
        u for u in resp.json()["data"]["items"] if u["username"] == "toggleuser"
    )
    resp = api_client.put(f"/api/users/{target['id']}", json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False
    resp = api_client.put(f"/api/users/{target['id']}", json={"is_active": True})
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is True
def test_admin_cannot_disable_self(api_client):
    _login_default_admin(api_client)
    me = api_client.get("/api/auth/me").json()["data"]
    resp = api_client.put(f"/api/users/{me['id']}", json={"is_active": False})
    assert resp.status_code == 400
def test_update_nonexistent_user_404(api_client):
    _login_default_admin(api_client)
    resp = api_client.put("/api/users/nope", json={"role": "teacher"})
    assert resp.status_code == 404
def test_update_rejects_invalid_role(api_client):
    _login_default_admin(api_client)
    resp = api_client.put("/api/users/some-id", json={"role": "superuser"})
    assert resp.status_code == 422
def test_teacher_cannot_update_user_403(api_client):
    _override_role("teacher")
    try:
        resp = api_client.put("/api/users/any-id", json={"role": "teacher"})
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_disabled_user_cannot_login(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/auth/register", json={
        "username": "disablelogin",
        "password": "password123",
    })
    resp = api_client.get("/api/users")
    target = next(
        u for u in resp.json()["data"]["items"] if u["username"] == "disablelogin"
    )
    api_client.put(f"/api/users/{target['id']}", json={"is_active": False})
    api_client.post("/api/auth/logout")
    resp = api_client.post("/api/auth/login", json={
        "username": "disablelogin",
        "password": "password123",
    })
    assert resp.status_code == 403