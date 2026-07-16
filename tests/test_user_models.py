import pytest
from pydantic import ValidationError
from app.models.user import Role, UserLogin, UserRegister, UserUpdate
def test_valid_register():
    u = UserRegister(username="alice", password="password123")
    assert u.username == "alice"
def test_register_rejects_short_username():
    with pytest.raises(ValidationError):
        UserRegister(username="ab", password="password123")
def test_register_rejects_short_password():
    with pytest.raises(ValidationError):
        UserRegister(username="alice", password="short")
def test_register_does_not_accept_role():
    u = UserRegister(username="alice", password="password123", role="admin")
    assert not hasattr(u, "role")
def test_login_requires_non_empty():
    with pytest.raises(ValidationError):
        UserLogin(username="", password="password123")
    with pytest.raises(ValidationError):
        UserLogin(username="alice", password="")
def test_user_update_allows_partial():
    u = UserUpdate(role=Role.TEACHER)
    assert u.role == Role.TEACHER
    assert u.is_active is None
def test_user_update_rejects_invalid_role():
    with pytest.raises(ValidationError):
        UserUpdate(role="superuser")