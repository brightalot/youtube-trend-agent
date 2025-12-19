from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import csv
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

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

class AnalysisRequest(BaseModel):
    focus_point: str

@app.post("/api/run-analysis") # URL prefix 통일성을 위해 /api 추가 추천
async def run_analysis(request: AnalysisRequest):
    if not N8N_WEBHOOK_URL:
        raise HTTPException(status_code=500, detail="Server misconfiguration: Webhook URL missing")
    
    async with httpx.AsyncClient() as client:
        try:
            # n8n Webhook Node 설정을 'Respond Immediately'로 해야 함
            response = await client.post(
                N8N_WEBHOOK_URL,
                json={"focus_point": request.focus_point},
                timeout=10.0 # n8n이 응답만 주면 되므로 짧아도 됨
            )
            response.raise_for_status()
        except httpx.ReadTimeout:
             # n8n이 작업을 시작했지만 응답이 늦는 경우 (성공으로 간주할 수도 있음)
            raise HTTPException(status_code=504, detail="n8n trigger timed out, but workflow might be running.")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to connect to n8n: {str(exc)}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"n8n returned error: {exc}")

    return {"status": "Analysis triggered", "message": "Request sent to n8n successfully."}

@app.get("/api/get-results")
def get_results():
    file_path = "/data/results.csv"
    
    if not os.path.exists(file_path):
        return {"status": "No results yet", "data": []}
    
    results = []
    try:
        # utf-8-sig로 변경하여 한글 호환성 강화
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # 빈 파일이거나 헤더만 있는 경우 처리
            if not reader.fieldnames:
                 return {"status": "Empty file", "data": []}
                 
            for row in reader:
                results.append(row)
    except Exception as e:
        print(f"Error reading CSV: {e}") # 로그 남기기
        raise HTTPException(status_code=500, detail=f"Error reading results file")
        
    return {"status": "Success", "data": results}