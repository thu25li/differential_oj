import pytest
from app.repositories.submission_repository import submission_repository
from app.utils.id_gen import generate_uuid
from app.utils.time import now_utc
def _make_sub(pid="P1001", uid="user-1", source="print(1)\n"):
    return {
        "id": generate_uuid(),
        "user_id": uid,
        "problem_id": pid,
        "language": "python",
        "source_code": source,
        "status": "pending",
        "created_at": now_utc(),
    }
async def test_create_and_get(fresh_db):
    s = _make_sub()
    await submission_repository.create(s)
    fetched = await submission_repository.get_by_id(s["id"])
    assert fetched is not None
    assert fetched["status"] == "pending"
    assert fetched["result"] is None
    assert fetched["score"] == 0
    assert fetched["total_time"] is None
    assert fetched["source_code"] == "print(1)\n"
async def test_get_nonexistent_returns_none(fresh_db):
    assert await submission_repository.get_by_id("nope") is None
async def test_list_excludes_source_code(fresh_db):
    for i in range(3):
        await submission_repository.create(_make_sub(pid=f"P{i}"))
    items, total = await submission_repository.list(page=1, page_size=10)
    assert total == 3
    for item in items:
        assert "source_code" not in item
async def test_list_filters(fresh_db):
    await submission_repository.create(_make_sub(pid="P1", uid="alice"))
    await submission_repository.create(_make_sub(pid="P2", uid="bob"))
    await submission_repository.create(_make_sub(pid="P1", uid="bob"))
    items, total = await submission_repository.list(problem_id="P1")
    assert total == 2
    items, total = await submission_repository.list(user_id="alice")
    assert total == 1
    assert items[0]["user_id"] == "alice"
    items, total = await submission_repository.list(problem_id="P1", user_id="bob")
    assert total == 1
async def test_list_status_filter(fresh_db):
    s = _make_sub()
    await submission_repository.create(s)
    await submission_repository.update_status(s["id"], "running", started_at=now_utc())
    items, total = await submission_repository.list(status="pending")
    assert total == 0
    items, total = await submission_repository.list(status="running")
    assert total == 1
async def test_update_status_running(fresh_db):
    s = _make_sub()
    await submission_repository.create(s)
    ts = now_utc()
    ok = await submission_repository.update_status(s["id"], "running", started_at=ts)
    assert ok is True
    fetched = await submission_repository.get_by_id(s["id"])
    assert fetched["status"] == "running"
    assert fetched["started_at"] == ts
async def test_update_result_finished(fresh_db):
    s = _make_sub()
    await submission_repository.create(s)
    ts = now_utc()
    ok = await submission_repository.update_result(
        s["id"], result="AC", score=100, total_time=0.15, finished_at=ts
    )
    assert ok is True
    fetched = await submission_repository.get_by_id(s["id"])
    assert fetched["status"] == "finished"
    assert fetched["result"] == "AC"
    assert fetched["score"] == 100
    assert fetched["total_time"] == 0.15
async def test_update_result_se_marks_failed(fresh_db):
    s = _make_sub()
    await submission_repository.create(s)
    ok = await submission_repository.update_result(
        s["id"], result="SE", score=0, total_time=0.0, finished_at=now_utc()
    )
    assert ok is True
    fetched = await submission_repository.get_by_id(s["id"])
    assert fetched["status"] == "failed"
    assert fetched["result"] == "SE"
async def test_reset_for_rejudge(fresh_db):
    s = _make_sub()
    await submission_repository.create(s)
    await submission_repository.update_result(
        s["id"], result="AC", score=100, total_time=0.1, finished_at=now_utc()
    )
    ok = await submission_repository.reset_for_rejudge(s["id"])
    assert ok is True
    fetched = await submission_repository.get_by_id(s["id"])
    assert fetched["status"] == "pending"
    assert fetched["result"] is None
    assert fetched["score"] == 0
    assert fetched["total_time"] is None
    assert fetched["started_at"] is None
    assert fetched["finished_at"] is None
    assert fetched["source_code"] == "print(1)\n"
async def test_pagination(fresh_db):
    for i in range(5):
        await submission_repository.create(_make_sub(pid=f"P{i}"))
    items, total = await submission_repository.list(page=2, page_size=2)
    assert total == 5
    assert len(items) == 2