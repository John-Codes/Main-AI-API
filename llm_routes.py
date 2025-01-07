from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from auth import Authentication, UserInDB
import datetime
import os
from openai import OpenAI
from month_goal import MonthGoal
from db import get_db, DatabaseConnection

def get_db_path():
    return os.getenv("DATABASE_PATH", "test_database.db")

llm_router = APIRouter(tags=["llm"])
auth_service = Authentication()

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPEN_ROUTER"),
)

async def call_openrouter(prompt: str):
    completion = openrouter_client.chat.completions.create(
        model="meta-llama/llama-3.1-70b-instruct:free",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return completion.choices[0].message.content

async def get_month_goal_data(token: str) -> dict:
    """Get the user's month goal data"""
    try:
        with DatabaseConnection(get_db_path()) as db:
            month_goal_service = MonthGoal(db=db, auth=auth_service)
            return month_goal_service.get_goal_with_countdown(token) or {}
    except Exception as e:
        print(f"Error getting month goal: {str(e)}")
        return {}

def create_llm_authenticated_json_response(llm_response: str, goal: str = None, created_at: str = None, days_left: int = None):
    return JSONResponse({
        "llm_response": llm_response,
        "goal": goal,
        "created_at": created_at,
        "days_left": days_left
    })

async def get_llm_prompt_context(authorization_header: str) -> str:
    goal_data = await get_month_goal_data(authorization_header)
    if goal_data and goal_data.get('goal'):
        return f"{goal_data.get('goal', '')} (Created: {goal_data.get('created_at', '')}, Days Left: {goal_data.get('days_left', '')})"
    return None

@llm_router.get("/llm_protected")
async def llm_protected(prompt: str, request: Request):
    authorization_header = request.headers.get("Authorization")
    if authorization_header and authorization_header.startswith("Bearer "):
        try:
            token = authorization_header.split(" ")[1]
            goal_context = await get_month_goal_data(token)
            full_prompt = f"{prompt}\n\nMy current month goal: {goal_context}" if goal_context and goal_context.get('goal') else prompt
            llm_response = await call_openrouter(full_prompt)
            return create_llm_authenticated_json_response(llm_response, goal_context.get('goal') if goal_context else None, goal_context.get("created_at") if goal_context else None, goal_context.get("days_left") if goal_context else None)
        except HTTPException as e:
            llm_response = await call_openrouter(prompt)
            return create_llm_authenticated_json_response(f"<b>Please Log in</b> {llm_response}" if llm_response else "<b>Please Log in</b> An error occurred.")
        except Exception as e:
            return create_llm_authenticated_json_response(detail=str(e))
    else:
        llm_response = await call_openrouter(prompt)
        return create_llm_authenticated_json_response(llm_response=f"<b>Please Log in</b> {llm_response}" if llm_response else "<b>Please Log in</b> An error occurred.")
