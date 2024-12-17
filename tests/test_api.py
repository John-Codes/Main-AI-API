#pytest -s tests/test_api.py
import pytest
import uuid
from httpx import AsyncClient
from main import app
from db import get_db, init_db, DatabaseConnection
import os  # Import os module to remove the test database file
import pytest_asyncio

# ANSI escape codes for colors
BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def colored_print(text, color):
    print(f"{color}{text}{RESET}")

@pytest.fixture(scope="function")
def test_db():
    # Setup: Create a fresh test database and initialize it
    db_path = f"test_database_{uuid.uuid4()}.db"
    with DatabaseConnection(db_path) as conn:
        init_db(conn)
    yield db_path
    # Teardown: Remove the test database file after the test
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest_asyncio.fixture
async def client(test_db):
    # Override the database connection to use the test database
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

@pytest.mark.asyncio
async def test_signup(client):
    colored_print("Testing signup...", BLUE)
    # Generate a unique email
    user_email = f"testuser{uuid.uuid4()}@example.com"
    user_data = {
        "email": user_email,
        "password": "password123"
    }
    response = await client.post("/auth/signup", json=user_data)
    print(f"Signup response: {response.json()}")
    if response.status_code == 200:
        colored_print("Signup successful", GREEN)
    else:
        colored_print("Signup failed", RED)
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "User created successfully"

@pytest.mark.asyncio
async def test_login(client):
    colored_print("Testing login...", BLUE)
    # Sign up a user
    user_email = f"testuser{uuid.uuid4()}@example.com"
    user_data = {
        "email": user_email,
        "password": "password123"
    }
    signup_response = await client.post("/auth/signup", json=user_data)
    print(f"Signup response: {signup_response.json()}")
    assert signup_response.status_code == 200

    # Login using the token endpoint
    login_data = {
        "username": user_email,
        "password": "password123"
    }
    login_response = await client.post("/auth/token", data=login_data)
    print(f"Login response: {login_response.json()}")
    if login_response.status_code == 200:
        colored_print("Login successful", GREEN)
    else:
        colored_print("Login failed", RED)
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    colored_print("Testing login with invalid credentials...", BLUE)
    # Use incorrect credentials
    login_data = {
        "username": "nonexistentuser@example.com",
        "password": "wrongpassword"
    }
    login_response = await client.post("/auth/token", data=login_data)
    print(f"Invalid login response: {login_response.json()}")
    if login_response.status_code == 401:
        colored_print("Invalid login test successful", GREEN)
    else:
        colored_print("Invalid login test failed", RED)
    assert login_response.status_code == 401  # Unauthorized

@pytest.mark.asyncio
async def test_protected_endpoint(client):
    colored_print("Testing protected endpoint...", BLUE)
    # Sign up a user
    user_email = f"testuser{uuid.uuid4()}@example.com"
    user_data = {
        "email": user_email,
        "password": "password123"
    }
    signup_response = await client.post("/auth/signup", json=user_data)
    print(f"Signup response: {signup_response.json()}")
    assert signup_response.status_code == 200

    # Login using the token endpoint
    login_data = {
        "username": user_email,
        "password": "password123"
    }
    login_response = await client.post("/auth/token", data=login_data)
    print(f"Login response: {login_response.json()}")
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Access the protected endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    protected_response = await client.get("/protected", headers=headers)
    print(f"Protected response: {protected_response.json()}")
    if protected_response.status_code == 200:
        colored_print("Protected endpoint test successful", GREEN)
    else:
        colored_print("Protected endpoint test failed", RED)
    assert protected_response.status_code == 200
    assert "user_email" in protected_response.json()
    assert protected_response.json()["user_email"] == user_email

@pytest.mark.asyncio
async def test_protected_endpoint_no_auth(client):
    colored_print("Testing protected endpoint without authentication...", BLUE)
    # Access the protected endpoint without authentication
    protected_response = await client.get("/protected")
    print(f"Unauthorized protected response: {protected_response.json()}")
    if protected_response.status_code == 401:
        colored_print("Unauthorized protected endpoint test successful", GREEN)
    else:
        colored_print("Unauthorized protected endpoint test failed", RED)
    assert protected_response.status_code == 401  # Unauthorized

@pytest.mark.asyncio
async def test_search_endpoint_no_auth(client):
    colored_print("Testing search endpoint without authentication...", BLUE)
    # Access the search endpoint without authentication
    search_response = await client.get("/search?query=test")
    print(f"Unauthorized search response: {search_response.json()}")
    if search_response.status_code == 401:
        colored_print("Unauthorized search endpoint test successful", GREEN)
    else:
        colored_print("Unauthorized search endpoint test failed", RED)
    assert search_response.status_code == 401  # Unauthorized

@pytest.mark.asyncio
async def test_search_endpoint(client):
    colored_print("Testing search endpoint...", BLUE)
    # Sign up a user
    user_email = f"testuser{uuid.uuid4()}@example.com"
    user_data = {
        "email": user_email,
        "password": "password123"
    }
    signup_response = await client.post("/auth/signup", json=user_data)
    print(f"Signup response: {signup_response.json()}")
    assert signup_response.status_code == 200

    # Login using the token endpoint
    login_data = {
        "username": user_email,
        "password": "password123"
    }
    login_response = await client.post("/auth/token", data=login_data)
    print(f"Login response: {login_response.json()}")
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Access the search endpoint with a valid token
    headers = {"Authorization": f"Bearer {access_token}"}
    colored_print("Searching for 'test'...", BLUE)
    search_response = await client.get("/search?query=test", headers=headers)
    print(f"Search response: {search_response.json()}")
    if search_response.status_code == 200:
        colored_print("Search endpoint test successful", GREEN)
    else:
        colored_print("Search endpoint test failed", RED)
    assert search_response.status_code == 200
    assert isinstance(search_response.json(), list)


@pytest.mark.asyncio
async def test_llm_protected_endpoint(client):
    colored_print("Testing protected LLM endpoint...", BLUE)
    # Sign up a user
    user_email = f"testuser{uuid.uuid4()}@example.com"
    user_data = {
        "email": user_email,
        "password": "password123"
    }
    signup_response = await client.post("/auth/signup", json=user_data)
    print(f"Signup response: {signup_response.json()}")
    assert signup_response.status_code == 200

    # Login using the token endpoint
    login_data = {
        "username": user_email,
        "password": "password123"
    }
    login_response = await client.post("/auth/token", data=login_data)
    print(f"Login response: {login_response.json()}")
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Access the protected LLM endpoint with a valid token
    headers = {"Authorization": f"Bearer {access_token}"}
    prompt = "What is the meaning of life?"
    protected_response = await client.get(f"/llm_protected?prompt={prompt}", headers=headers)
    print(f"Protected LLM response: {protected_response.json()}")
    if protected_response.status_code == 200:
        colored_print("Protected LLM endpoint test successful", GREEN)
    else:
        colored_print("Protected LLM endpoint test failed", RED)
    assert protected_response.status_code == 200
    assert protected_response.json() is not None
    assert isinstance(protected_response.json(), str)

@pytest.mark.asyncio
async def test_llm_protected_endpoint_no_auth(client):
    colored_print("Testing protected LLM endpoint without authentication...", BLUE)
    prompt = "What is the meaning of life?"
    # Access the protected LLM endpoint without authentication
    protected_response = await client.get(f"/llm_protected?prompt={prompt}")
    print(f"Unauthorized protected LLM response: {protected_response.text}")
    if protected_response.status_code == 200:
        colored_print("Unauthorized protected LLM endpoint test successful", GREEN)
    else:
        colored_print("Unauthorized protected LLM endpoint test failed", RED)
    assert protected_response.status_code == 200
    assert "Please Log in" in protected_response.text


