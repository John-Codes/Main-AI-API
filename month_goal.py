from typing import Optional
from fastapi import Depends, HTTPException, status
from db import get_db
from auth import Authentication
from jose import JWTError
from datetime import datetime, timedelta, timezone




class MonthGoal:
    def __init__(self, db=Depends(get_db), auth=Depends(Authentication)):
        self.db = db
        self.auth = auth
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_goals (
                user_id INTEGER PRIMARY KEY,
                goal TEXT,
                created_at TEXT
            )
        """)
        self.db.commit()

    def _get_user_id_from_token(self, token: str) -> int:
        try:
            payload = self.auth.decode_token(token)
            return payload.get("id")
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    def create_goal(self, token: str, goal: str, created_at: str):
        user_id = self._get_user_id_from_token(token)
        if not created_at:
            created_at = datetime.now(timezone.utc).isoformat()
        cursor = self.db.cursor()
        cursor.execute("INSERT OR REPLACE INTO monthly_goals (user_id, goal, created_at) VALUES (?, ?, ?)", (user_id, goal, created_at))
        self.db.commit()
        return {"message": "Goal created/updated successfully"}

    def read_goal(self, token: str) -> Optional[tuple[str, str]]:
        user_id = self._get_user_id_from_token(token)
        cursor = self.db.cursor()
        cursor.execute("SELECT goal, created_at FROM monthly_goals WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result if result else None

    def update_goal(self, token: str, new_goal: str):
        user_id = self._get_user_id_from_token(token)
        cursor = self.db.cursor()
        cursor.execute("UPDATE monthly_goals SET goal = ? WHERE user_id = ?", (new_goal, user_id))
        self.db.commit()
        return {"message": "Goal updated successfully"}

    def delete_goal(self, token: str):
        user_id = self._get_user_id_from_token(token)
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM monthly_goals WHERE user_id = ?", (user_id,))
        self.db.commit()
        return {"message": "Goal deleted successfully"}
    
    def _calculate_countdown(self, created_at: str):
        created_date = datetime.fromisoformat(created_at)
        target_date = created_date + timedelta(days=31)
        days_left = (target_date - datetime.now(timezone.utc)).days
        return max(days_left, 0)

    def get_goal_with_countdown(self, token: str) -> Optional[dict]:
        user_id = self._get_user_id_from_token(token)
        cursor = self.db.cursor()
        cursor.execute("SELECT goal, created_at FROM monthly_goals WHERE user_id = ?", (user_id,))
        goal_data = cursor.fetchone()
        if goal_data:
            goal, created_at = goal_data
            days_left = self._calculate_countdown(created_at)
            return {
                "goal": goal,
                "created_at": created_at,
                "days_left": days_left,
            }
        return None
