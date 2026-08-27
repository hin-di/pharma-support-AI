import os
import json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from app.models.schemas import PharmacyMetrics, PatientCondition
from app.rules.regional_support import evaluate_regional_support, get_default_metrics
from app.rules.patient_billing import evaluate_patient_billing

app = FastAPI(title="Pharma Support AI - 薬局業務・加算管理システム")

# Mount static and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

MOCK_DATA_PATH = "data/mock_data.json"

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/metrics")
def get_metrics():
    if os.path.exists(MOCK_DATA_PATH):
        with open(MOCK_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    return get_default_metrics().model_dump()

@app.post("/api/metrics")
def save_metrics(metrics: PharmacyMetrics):
    os.makedirs("data", exist_ok=True)
    with open(MOCK_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics.model_dump(), f, ensure_ascii=False, indent=2)
    return {"status": "saved"}

@app.post("/api/evaluate-regional")
def api_evaluate_regional(metrics: PharmacyMetrics):
    result = evaluate_regional_support(metrics)
    return result

@app.post("/api/suggest-patient-billing")
def api_suggest_patient_billing(condition: PatientCondition):
    result = evaluate_patient_billing(condition)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
