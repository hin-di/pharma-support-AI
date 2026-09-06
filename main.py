import os
import json
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from app.models.schemas import PharmacyMetrics, PatientCondition
from app.rules.regional_support import evaluate_regional_support, get_default_metrics
from app.rules.patient_billing import evaluate_patient_billing
from app.parsers.uke_parser import parse_uke_content
from app.parsers.csv_parser import parse_csv_content

app = FastAPI(title="Pharma Support AI - 令和8年度改定完全準拠版")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

MOCK_DATA_PATH = "data/mock_data.json"

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/metrics")
def get_metrics():
    if os.path.exists(MOCK_DATA_PATH):
        try:
            with open(MOCK_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass
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

@app.post("/api/import-file")
async def api_import_file(file: UploadFile = File(...)):
    content_bytes = await file.read()
    filename = file.filename or ""
    
    try:
        content = content_bytes.decode('cp932')
    except UnicodeDecodeError:
        content = content_bytes.decode('utf-8', errors='ignore')
        
    if filename.lower().endswith('.uke') or 'IR,' in content[:100] or 'RE,' in content[:200]:
        parsed = parse_uke_content(content)
    else:
        parsed = parse_csv_content(content)
        
    return {
        "status": "success",
        "filename": filename,
        "parsed_data": parsed
    }

@app.post("/api/sample-import")
def api_sample_import():
    sample_result = {
        "format": "レセプト電算データ (UKE解析シミュレーション)",
        "monthly_prescriptions": 1350,
        "generic_percentage": 87.2,
        "rec_1_night_holiday_count": 52,
        "rec_2_narcotics_count": 4,
        "rec_3_prevention_adjustment_count": 35,
        "rec_4_guidance_1a_2a_count": 38,
        "rec_5_outpatient_support_1_count": 3,
        "rec_6_home_visit_count": 28,
        "rec_7_info_provision_tr_count": 42,
        "rec_8_pediatric_special_count": 2,
        "rec_9_multidisciplinary_conference_count": 2,
        "message": "レセプト電算データから実績9項目及び後発品87.2%を抽出・集計しました。"
    }
    return {
        "status": "success",
        "filename": "202608_RECEIPT.UKE",
        "parsed_data": sample_result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
