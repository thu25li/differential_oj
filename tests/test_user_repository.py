import pytest
from app.repositories.user_repository import user_repository
from app.utils.id_gen import generate_uuid
from app.utils.password import hash_password
from app.utils.time import now_utc
def _make_user(username="alice", role="student"):
    ts = now_utc()
    return {
        "id": generate_uuid(),
        "username": username,
        "password_hash": hash_password("password123"),
        "role": role,
        "is_active": True,
        "created_at": ts,
        "updated_at": ts,
    }
async def test_create_and_get_by_id(fresh_db):
    u = _make_user()
    await user_repository.create(u)
    fetched = await user_repository.get_by_id(u["id"])
    assert fetched is not None
    assert fetched["username"] == "alice"
    assert fetched["password_hash"].startswith("$2b$")
    assert fetched["role"] == "student"
async def test_get_by_username(fresh_db):
    u = _make_user(username="bob")
    await user_repository.create(u)
    fetched = await user_repository.get_by_username("bob")
    assert fetched is not None
    assert fetched["id"] == u["id"]
async def test_get_nonexistent_returns_none(fresh_db):
    assert await user_repository.get_by_id("nope") is None
    assert await user_repository.get_by_username("ghost") is None
async def test_create_duplicate_username_raises(fresh_db):
    u = _make_user(username="dup")
    await user_repository.create(u)
    u2 = _make_user(username="dup")
    with pytest.raises(Exception):
        await user_repository.create(u2)
async def test_list_excludes_password_hash(fresh_db):
    for name in ["a", "b", "c"]:
        await user_repository.create(_make_user(username=name))
    items, total = await user_repository.list(page=1, page_size=10)
    assert total == 4
    assert len(items) == 4
    for item in items:
        assert "password_hash" not in item
async def test_list_pagination(fresh_db):
    for i in range(5):
        await user_repository.create(_make_user(username=f"u{i}"))
    items, total = await user_repository.list(page=2, page_size=2)
    assert total == 6
    assert len(items) == 2
async def test_update_role_and_active(fresh_db):
    u = _make_user()
    await user_repository.create(u)
    ok = await user_repository.update(u["id"], {
        "role": "teacher",
        "is_active": False,
        "updated_at": now_utc(),
    })
    assert ok is True
    fetched = await user_repository.get_by_id(u["id"])
    assert fetched["role"] == "teacher"
    assert fetched["is_active"] is False
async def test_update_nonexistent_returns_false(fresh_db):
    ok = await user_repository.update("nope", {"role": "teacher", "updated_at":
now_utc()})
    assert ok is False
async def test_count_admins(fresh_db):
    await user_repository.create(_make_user(username="s1", role="student"))
    await user_repository.create(_make_user(username="t1", role="teacher"))
    await user_repository.create(_make_user(username="a1", role="admin"))
    assert await user_repository.count_admins() == 2
async def test_username_exists(fresh_db):
    await user_repository.create(_make_user(username="special"))
    assert await user_repository.username_exists("special") is True
    assert await user_repository.username_exists("notthere") is False