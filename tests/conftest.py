import pytest
import os
import sys
from httpx import AsyncClient
from db import get_db, init_db, DATABASE_URL
import pytest_asyncio
from month_goal import MonthGoal
from auth import Authentication
import uuid
import sqlite3
from fastapi import FastAPI
from main import app  # Import the app instance

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure pytest settings
def pytest_configure(config):
    config.option.asyncio_default_loop_scope = "function"

# Database fixture
@pytest.fixture(scope="function")
def test_db():
    # Setup: Create a fresh test database
    db_path = f"test_database_{uuid.uuid4()}.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    global DATABASE_URL
    DATABASE_URL = db_path
    conn = sqlite3.connect(db_path)  # Create connection here
    yield db_path
    # Teardown: Remove the test database file after the test
    if os.path.exists(db_path):
        os.remove(db_path)
    conn.close()  # Close the connection

# Test client fixture
@pytest_asyncio.fixture
async def client(test_db):
    # Initialize the database for testing
    conn = sqlite3.connect(test_db)  # Connect to the test database
    init_db(conn)
    conn.close()
    async with AsyncClient(app=app, base_url="http://testserver") as test_client:
        yield test_client

@pytest.fixture
def test_month_goal(test_db, auth):
    conn = sqlite3.connect(test_db)
    yield MonthGoal(db=conn, auth=auth)
    conn.close()
