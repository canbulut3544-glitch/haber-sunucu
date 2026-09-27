from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import database, models
from api import routes
from services.news_fetcher import fetch_and_store_mock_news
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)

# Create tables
models.Base.metadata.create_all(bind=database.engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Fetch mock data
    db = database.SessionLocal()
    fetch_and_store_mock_news(db)
    db.close()
    yield
    # Shutdown
    pass

app = FastAPI(title="Finance News Backend", lifespan=lifespan)

# Allow CORS if needed, though mobile apps don't strictly require it. 
# We restrict to specific origins in production if there is a web version.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Finance News API is running. Access via Mobile App only."}
