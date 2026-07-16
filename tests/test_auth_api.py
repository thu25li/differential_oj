import pytest
def test_register_201(api_client):
    resp = api_client.post("/api/auth/register", json={
        "username": "newstudent",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["username"] == "newstudent"
    assert data["role"] == "student"
    assert data["is_active"] is True
    assert "password_hash" not in data
def test_register_duplicate_409(api_client):
    api_client.post("/api/auth/register", json={
        "username": "dupuser",
        "password": "password123",
    })
    resp = api_client.post("/api/auth/register", json={
        "username": "dupuser",
        "password": "different123",
    })
    assert resp.status_code == 409
def test_register_short_password_422(api_client):
    resp = api_client.post("/api/auth/register", json={
        "username": "validuser",
        "password": "short",
    })
    assert resp.status_code == 422
def test_register_cannot_self_assign_role(api_client):
    resp = api_client.post("/api/auth/register", json={
        "username": "hacker",
        "password": "password123",
        "role": "admin",
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["role"] == "student"
def test_login_success(api_client):
    api_client.post("/api/auth/register", json={
        "username": "loginuser",
        "password": "password123",
    })
    resp = api_client.post("/api/auth/login", json={
        "username": "loginuser",
        "password": "password123",
    })
    assert resp.status_code == 200
def test_login_wrong_password_401(api_client):
    api_client.post("/api/auth/register", json={
        "username": "loginuser2",
        "password": "password123",
    })
    resp = api_client.post("/api/auth/login", json={
        "username": "loginuser2",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401
    assert "username" not in resp.json()["message"].lower()
def test_login_nonexistent_user_401(api_client):
    resp = api_client.post("/api/auth/login", json={
        "username": "ghost",
        "password": "whatever",
    })
    assert resp.status_code == 401
def test_me_requires_login_401(api_client):
    resp = api_client.get("/api/auth/me")
    assert resp.status_code == 401
def test_me_after_login(api_client):
    api_client.post("/api/auth/register", json={
        "username": "meuser",
        "password": "password123",
    })
    api_client.post("/api/auth/login", json={
        "username": "meuser",
        "password": "password123",
    })
    resp = api_client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["username"] == "meuser"
    assert "password_hash" not in data
def test_logout_clears_session(api_client):
    api_client.post("/api/auth/register", json={
        "username": "logoutuser",
        "password": "password123",
    })
    api_client.post("/api/auth/login", json={
        "username": "logoutuser",
        "password": "password123",
    })
    assert api_client.get("/api/auth/me").status_code == 200
    resp = api_client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert api_client.get("/api/auth/me").status_code == 401
def test_default_admin_can_login(api_client):
    resp = api_client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin12345",
    })
    assert resp.status_code == 200
    resp = api_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "admin"