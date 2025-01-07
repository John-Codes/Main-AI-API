from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from month_goal import MonthGoal

from datetime import datetime

month_goal_router = APIRouter(prefix="/month_goals", tags=["month_goals"])



@month_goal_router.post("/", status_code=status.HTTP_201_CREATED)
def create_month_goal(goal: str, token: str, month_goal: MonthGoal = Depends()):
    return month_goal.create_goal(token, goal, created_at=datetime.utcnow().isoformat() + 'Z')

@month_goal_router.get("/", response_model=Optional[tuple[str, str]])
def read_month_goal(token: str, month_goal: MonthGoal = Depends()):
    goal_data = month_goal.read_goal(token)
    if goal_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal_data

@month_goal_router.put("/")
def update_month_goal(new_goal: str, token: str, month_goal: MonthGoal = Depends()):
    return month_goal.update_goal(token, new_goal)

@month_goal_router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_month_goal(token: str, month_goal: MonthGoal = Depends()):
    return month_goal.delete_goal(token)
