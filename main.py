from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from db import init_db, get_db
from auth import Authentication
from auth_routes import auth_router
from search_routes import search_router
from llm_routes import llm_router
from month_goal_routes import month_goal_router

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

app.include_router(auth_router)
app.include_router(search_router)
app.include_router(llm_router)
app.include_router(month_goal_router)
