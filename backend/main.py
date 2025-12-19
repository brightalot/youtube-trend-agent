from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import router
from api import router

# Global config check
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 체크
    if not N8N_WEBHOOK_URL:
        print("⚠️ WARNING: N8N_WEBHOOK_URL is not set. Analysis features will fail.")
    yield
    # 서버 종료 시 정리 로직 (필요시)

app = FastAPI(lifespan=lifespan)

# Register router
app.include_router(router)