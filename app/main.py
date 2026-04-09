from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import admin
from app.routers import models, projects, events
import logging
import sys
from app.config.settings import settings
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.dependencies import limiter



logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if settings.debug_logs else logging.INFO)
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# Routers
app.include_router(admin.router)
app.include_router(models.router)
app.include_router(projects.router)
app.include_router(events.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/info")
async def info():
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email,
        "items_per_user": settings.items_per_user,
    }