import pytest
import os
from httpx import AsyncClient
from main import app
from db import get_db, DatabaseConnection, init_db
import pytest_asyncio

# Configure pytest settings
def pytest_configure(config):
    config.option.asyncio_default_loop_scope = "function"

# Database fixture
@pytest.fixture(scope="function")
def test_db():
    # Setup: Create a fresh test database and initialize it
    db_path = "test_database.db"
    with DatabaseConnection(db_path) as conn:
        init_db(conn)
    yield db_path
    # Teardown: Remove the test database file after the test
    if os.path.exists(db_path):
        os.remove(db_path)

# Override the get_db dependency
@pytest_asyncio.fixture
async def override_get_db(test_db):
    async def _override_get_db():
        db_path = test_db
        with DatabaseConnection(db_path) as conn:
            yield conn
    app.dependency_overrides[get_db] = _override_get_db
    yield
    del app.dependency_overrides[get_db]

# Test client fixture using the overridden dependencies
@pytest_asyncio.fixture
async def client(override_get_db):
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
