import pytest
from datetime import datetime
from auth import Authentication
import pytest_asyncio

@pytest_asyncio.fixture
async def auth():
    return Authentication()

@pytest.mark.asyncio
async def test_create_month_goal_with_timestamp(client, auth):
    auth_service = Authentication()
    access_token = auth_service.create_access_token(data={"id": 1})
    timestamp = datetime.now().isoformat()
    response = await client.post("/month_goals/", params={"goal": "Test Goal", "token": access_token}, json={"timestamp": timestamp})
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_read_month_goal(client, auth):
    auth_service = Authentication()
    access_token = auth_service.create_access_token(data={"id": 1})
    # First create a month goal
    timestamp = datetime.now().isoformat()
    create_response = await client.post("/month_goals/", params={"goal": "Test Goal", "token": access_token}, json={"timestamp": timestamp})
    assert create_response.status_code == 201
    # Then read the month goal
    read_response = await client.get("/month_goals/", params={"token": access_token})
    assert read_response.status_code == 200
    assert read_response.json() == ["Test Goal", timestamp + 'Z']

@pytest.mark.asyncio
async def test_update_month_goal(client, auth):
    auth_service = Authentication()
    access_token = auth_service.create_access_token(data={"id": 1})
    # First create a month goal
    timestamp = datetime.now().isoformat()
    create_response = await client.post("/month_goals/", params={"goal": "Original Goal", "token": access_token}, json={"timestamp": timestamp})
    assert create_response.status_code == 201
    # Then update the month goal
    update_response = await client.put("/month_goals/", params={"new_goal": "Updated Goal", "token": access_token})
    assert update_response.status_code == 200
    # Read the month goal to verify it's updated
    read_response = await client.get("/month_goals/", params={"token": access_token})
    assert read_response.status_code == 200
    assert read_response.json() == ["Updated Goal", timestamp + 'Z']

@pytest.mark.asyncio
async def test_delete_month_goal(client, auth):
    auth_service = Authentication()
    access_token = auth_service.create_access_token(data={"id": 1})
    # First create a month goal
    timestamp = datetime.now().isoformat()
    create_response = await client.post("/month_goals/", params={"goal": "Goal to Delete", "token": access_token}, json={"timestamp": timestamp})
    assert create_response.status_code == 201
    # Then delete the month goal
    delete_response = await client.delete("/month_goals/", params={"token": access_token})
    assert delete_response.status_code == 204
    # Try to read the month goal to verify it's deleted
    read_response = await client.get("/month_goals/", params={"token": access_token})
    assert read_response.status_code == 404
