#pytest -s tests/test_api.py
import pytest
import uuid
from httpx import AsyncClient
from main import app
from db import get_db, init_db, DatabaseConnection
import os  # Import os module to remove the test database file
import pytest_asyncio
import asyncio
from month_goal import MonthGoal
from auth import Authentication
from datetime import datetime

# ANSI escape codes for colors
BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def colored_print(text, color):
    print(f"{color}{text}{RESET}")

import os
from dotenv import load_dotenv
import pytest_asyncio

load_dotenv()

@pytest_asyncio.fixture
async def client(test_db):
    # Override the database connection to use the test database
    os.environ["OPEN_ROUTER"] = os.getenv("OPEN_ROUTER")
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
    protected_response = await client.get("/auth/protected", headers=headers)
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
    protected_response = await client.get("/auth/protected")
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
async def test_llm_protected_endpoint(client, test_db):
    colored_print("Testing protected LLM endpoint...", BLUE)
    # Create database connection that will be used throughout the test
    with DatabaseConnection(test_db) as db:
        # Initialize services with the same database connection
        auth_service = Authentication()
        month_goal_service = MonthGoal(db=db, auth=auth_service)

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

        # Access the protected LLM endpoint without a goal set
        headers_no_goal = {"Authorization": f"Bearer {access_token}"}
        prompt_no_goal = "What is my goal?"
        protected_response_no_goal = await client.get(f"/llm_protected?prompt={prompt_no_goal}", headers=headers_no_goal)
        assert protected_response_no_goal.status_code == 200
        assert protected_response_no_goal.json()["llm_response"] == "I don't have any information about your goal. Our conversation just started. Could you please share more about what you're trying to achieve or what's on your mind? I'll do my best to help."

        # Create a goal
        month_goal_service.create_goal(token=access_token, goal="Test Goal", created_at=datetime.utcnow().isoformat() + 'Z')

        # Access the protected LLM endpoint with a valid token
        headers_with_goal = {"Authorization": f"Bearer {access_token}"}
        prompt_with_goal = "What is the meaning of life?"

        # Make the LLM protected request
        protected_response_with_goal = await client.get(f"/llm_protected?prompt={prompt_with_goal}", headers=headers_with_goal)
        print(f"Protected LLM response: {protected_response_with_goal.json()}")

        if protected_response_with_goal.status_code == 200:
            colored_print("Protected LLM endpoint test successful", GREEN)
        else:
            colored_print("Protected LLM endpoint test failed", RED)

        assert protected_response_with_goal.status_code == 200
        assert protected_response_with_goal.json() is not None
        # Check if the response is a dictionary
        assert isinstance(protected_response_with_goal.json(), dict)
        # Check if the response contains the expected keys
        assert 'goal' in protected_response_with_goal.json()
        assert 'created_at' in protected_response_with_goal.json()
        assert 'days_left' in protected_response_with_goal.json()
        assert 'llm_response' in protected_response_with_goal.json()

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
