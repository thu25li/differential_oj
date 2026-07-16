import tempfile
from pathlib import Path
import pytest_asyncio
import app.database as db_module
from app.database import close_database, init_database
@pytest_asyncio.fixture
async def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)
    original_path = db_module.DB_PATH
    db_module.DB_PATH = temp_path
    try:
        await init_database()
        yield
    finally:
        await close_database()
        if temp_path.exists():
            temp_path.unlink()
        db_module.DB_PATH = original_path
import pytest
@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient
    from app.main import app
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)
    original_path = db_module.DB_PATH
    db_module.DB_PATH = temp_path
    try:
        with TestClient(app) as c:
            yield c
    finally:
        if temp_path.exists():
            temp_path.unlink()
        db_module.DB_PATH = original_path