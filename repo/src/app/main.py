from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.config import config
from src.app.api.v1.router import api_v1_router

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
    description=config.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=config.API_V1_STR)

@app.get("/")
async def root():
    return {
        "title": config.PROJECT_NAME,
        "version": config.VERSION,
        "docs": "/docs",
        "api_v1": f"{config.API_V1_STR}/health"
    }
