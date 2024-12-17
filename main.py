from fastapi import FastAPI, Depends, HTTPException, status, Request
from contextlib import asynccontextmanager
from db import init_db, get_db
from auth import Authentication, UserCreate, PasswordReset, Token, UserInDB
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr
from search import bing_search, process_results
import os
from openai import OpenAI
from fastapi.responses import RedirectResponse, JSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database
    db_conn = get_db()
    init_db(db_conn)
    yield
    # Shutdown: Close database connections if necessary

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

auth = Authentication()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Routes
@app.post("/auth/signup")
def signup(user: UserCreate, db=Depends(get_db)):
    return auth.signup(user, db)

@app.post("/auth/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    return auth.login(form_data, db)

@app.post("/auth/reset-password")
def reset_password(reset_data: PasswordReset, db=Depends(get_db)):
    return auth.reset_password(reset_data, db)

@app.get("/protected")
async def protected(request: Request, current_user: UserInDB = Depends(auth.get_current_user)):
    return {"user_email": current_user.email}

@app.get("/search")
async def search(query: str, current_user: UserInDB = Depends(auth.get_current_user)):
    try:
        if not os.getenv('BING_API_KEY'):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="BING_API_KEY not found in .env file")
        results = bing_search(query)
        processed_results = process_results(results)
        return processed_results
    except Exception as e:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/llm_protected")
async def llm_protected(prompt: str, request: Request):
    authorization_header = request.headers.get("Authorization")
    try:
        if authorization_header:
            current_user: UserInDB = Depends(auth.get_current_user, use_cache=False)
            api_key = os.getenv("OPEN_ROUTER")
            if not api_key:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OPEN_ROUTER API key not found")
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            completion = client.chat.completions.create(
                model="meta-llama/llama-3.1-70b-instruct:free",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return completion.choices[0].message.content
        else:
            api_key = os.getenv("OPEN_ROUTER")
            if not api_key:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OPEN_ROUTER API key not found")
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            completion = client.chat.completions.create(
                model="meta-llama/llama-3.1-70b-instruct:free",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return f"<b>Please Log in</b> {completion.choices[0].message.content}"
    except HTTPException as e:
         api_key = os.getenv("OPEN_ROUTER")
         if not api_key:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OPEN_ROUTER API key not found")
         client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
         )
         completion = client.chat.completions.create(
            model="meta-llama/llama-3.1-70b-instruct:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
         )
         return f"<b>Please Log in</b> {completion.choices[0].message.content}"
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
