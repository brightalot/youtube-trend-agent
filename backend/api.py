from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import csv
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/api")

# N8N Webhook URL
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

class AnalysisRequest(BaseModel):
    focus_point: str

@router.post("/analyses", tags=["Analyses"])
async def create_analysis(request: AnalysisRequest):
    """분석 시작"""
    if not N8N_WEBHOOK_URL:
        raise HTTPException(status_code=500, detail="N8N_WEBHOOK_URL not configured")
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {"focus_point": request.focus_point}
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
        except httpx.ReadTimeout:
            raise HTTPException(status_code=504, detail="n8n trigger timed out, but workflow might be running.")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to connect to n8n: {str(exc)}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"n8n returned error: {exc}")

    return {"status": "Analysis triggered", "message": "Request sent to n8n successfully."}

@router.get("/results", tags=["Results"])
def get_results():
    """결과 조회"""
    file_path = "/data/results.csv"
    
    if not os.path.exists(file_path):
        return {"status": "No results yet", "data": []}
    
    results = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return {"status": "Empty file", "data": []}
                
            for row in reader:
                results.append(row)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading results file")
        
    return {"status": "Success", "data": results}

@router.post("/results", tags=["Results"])
async def save_results(request: dict):
    """n8n에서 결과 저장"""
    file_path = "/data/results.csv"
    
    # n8n sends { data: [...] }
    data = request if isinstance(request, list) else request.get("data", [])
    
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    
    try:
        with open(file_path, mode='w', encoding='utf-8', newline='') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        return {"status": "Success", "message": f"Saved {len(data)} records"}
    except Exception as e:
        print(f"Error saving CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving results file")
