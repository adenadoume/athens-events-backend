from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import events
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Athens Events API",
    description="Real-time concerts, DJ sets, parties and nightlife in Athens, Greece",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "athens-events"}
