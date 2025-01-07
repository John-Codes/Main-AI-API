from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from db import get_db
from auth import Authentication, UserCreate, PasswordReset, Token, UserInDB

auth_router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = Authentication()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@auth_router.post("/signup")
def signup(user: UserCreate, db=Depends(get_db)):
    return auth_service.signup(user, db)

@auth_router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    return auth_service.login(form_data, db)

@auth_router.post("/reset-password")
def reset_password(reset_data: PasswordReset, db=Depends(get_db)):
    return auth_service.reset_password(reset_data, db)

@auth_router.get("/protected")
async def protected(request: Request, current_user: UserInDB = Depends(auth_service.get_current_user)):
    return {"user_email": current_user.email}
