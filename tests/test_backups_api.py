import json
import time
from pathlib import Path
import pytest
from app import database as db_module
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
        {"case_id": "c1", "input": "1 2\n", "output": "3\n", "score": 100, "is_hidden": False},
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
def test_create_backup_returns_201(api_client):
    _login_default_admin(api_client)
    resp = api_client.post("/api/admin/backups")
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["backup_id"].startswith("backup_")
    assert "created_at" in data
def test_create_backup_writes_manifest_and_db(api_client):
    _login_default_admin(api_client)
    resp = api_client.post("/api/admin/backups")
    backup_id = resp.json()["data"]["backup_id"]
    backup_dir = db_module.DB_PATH.parent / "backups" / backup_id
    assert (backup_dir / "manifest.json").exists()
    assert (backup_dir / "oj.db").exists()
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["backup_id"] == backup_id
    assert manifest["storage_type"] == "sqlite"
    assert manifest["files"] == ["oj.db"]
    assert manifest["total_size_bytes"] > 0
def test_list_backups_returns_records(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/admin/backups")
    api_client.post("/api/admin/backups")
    resp = api_client.get("/api/admin/backups")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 2
    for item in data["items"]:
        assert item["backup_id"].startswith("backup_")
        assert "created_at" in item
        assert "total_size_bytes" in item
def test_backup_restore_reverts_data(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/problems", json=_VALID_PROBLEM)
    resp = api_client.post("/api/admin/backups")
    backup_id = resp.json()["data"]["backup_id"]
    api_client.delete("/api/problems/P1001")
    assert api_client.get("/api/problems/P1001").status_code == 404
    resp = api_client.post(f"/api/admin/backups/{backup_id}/restore")
    assert resp.status_code == 200
    resp = api_client.get("/api/problems/P1001")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == "P1001"
def test_backup_restore_nonexistent_404(api_client):
    _login_default_admin(api_client)
    resp = api_client.post("/api/admin/backups/nonexistent/restore")
    assert resp.status_code == 404
def test_backup_restore_corrupted_manifest_preserves_current(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/problems", json=_VALID_PROBLEM)
    resp = api_client.post("/api/admin/backups")
    backup_id = resp.json()["data"]["backup_id"]
    manifest = db_module.DB_PATH.parent / "backups" / backup_id / "manifest.json"
    manifest.write_text("NOT VALID JSON {{{", encoding="utf-8")
    resp = api_client.post(f"/api/admin/backups/{backup_id}/restore")
    assert resp.status_code == 400
    resp = api_client.get("/api/problems/P1001")
    assert resp.status_code == 200
    resp = api_client.get("/api/auth/me")
    assert resp.status_code == 200
def test_backup_restore_missing_manifest_preserves_current(api_client):
    _login_default_admin(api_client)
    resp = api_client.post("/api/admin/backups")
    backup_id = resp.json()["data"]["backup_id"]
    manifest = db_module.DB_PATH.parent / "backups" / backup_id / "manifest.json"
    manifest.unlink()
    resp = api_client.post(f"/api/admin/backups/{backup_id}/restore")
    assert resp.status_code == 400
    resp = api_client.get("/api/auth/me")
    assert resp.status_code == 200
def test_backup_restore_missing_db_file_preserves_current(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/problems", json=_VALID_PROBLEM)
    resp = api_client.post("/api/admin/backups")
    backup_id = resp.json()["data"]["backup_id"]
    db_backup = db_module.DB_PATH.parent / "backups" / backup_id / "oj.db"
    db_backup.unlink()
    resp = api_client.post(f"/api/admin/backups/{backup_id}/restore")
    assert resp.status_code == 400
    resp = api_client.get("/api/problems/P1001")
    assert resp.status_code == 200
def test_backup_requires_admin_403(api_client):
    _override_role("teacher")
    try:
        resp = api_client.post("/api/admin/backups")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_list_backups_requires_admin_403(api_client):
    _override_role("teacher")
    try:
        resp = api_client.get("/api/admin/backups")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_restore_requires_admin_403(api_client):
    _override_role("teacher")
    try:
        resp = api_client.post("/api/admin/backups/any/restore")
        assert resp.status_code == 403
    finally:
        _clear_override()
def test_create_backup_writes_audit(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/admin/backups")
    resp = api_client.get("/api/audit-logs?action=CREATE_BACKUP")
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) >= 1
def test_restore_backup_writes_audit(api_client):
    _login_default_admin(api_client)
    resp = api_client.post("/api/admin/backups")
    backup_id = resp.json()["data"]["backup_id"]
    api_client.post(f"/api/admin/backups/{backup_id}/restore")
    resp = api_client.get("/api/audit-logs?action=RESTORE_BACKUP")
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert any(item["target_id"] == backup_id for item in items)
async def test_restart_persists_data(api_client):
    _login_default_admin(api_client)
    api_client.post("/api/problems", json=_VALID_PROBLEM)
    from app.database import close_database, init_database
    await close_database()
    await init_database()
    resp = api_client.get("/api/problems/P1001")
    assert resp.status_code == 200
