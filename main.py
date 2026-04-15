# main.py

import re
import uvicorn

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from alert import trigger_alert
from ingest import load_dataframes
from drift_engine import compute_drift
from llm_explainer import explain_drift
from scheduler import start_scheduler
from db import init_db, save_report, get_all_reports, get_dashboard_stats


# -------------------------------
# App lifecycle
# -------------------------------
scheduler_started = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler_started

    init_db()

    if not scheduler_started:
        start_scheduler()
        scheduler_started = True

    yield


app = FastAPI(
    title="DataDrift Analyzer",
    description="LLM-powered data drift detection for tabular pipelines.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# Main Drift Endpoint
# -------------------------------
@app.post("/analyze")
async def analyze_drift(
    pipeline_name: str = Form(default="unnamed-pipeline"),
    reference_csv: UploadFile = File(...),
    current_csv: UploadFile = File(...),
):

    # ✅ Normalize pipeline name
    pipeline_name = re.sub(r"[^A-Z0-9]+", "-", pipeline_name.strip().upper())

    # Step 1 — Read files
    ref_bytes = await reference_csv.read()
    cur_bytes = await current_csv.read()

    # Step 2 — Ingest
    ref_df, cur_df, warnings = load_dataframes(ref_bytes, cur_bytes)

    # Step 3 — Compute drift
    metrics = compute_drift(ref_df, cur_df)

    # Step 4 — LLM explanation
    if metrics["number_of_drifted_columns"] > 0:
        explanation = explain_drift(metrics, pipeline_name)
    else:
        explanation = {
            "severity": "LOW",
            "summary": "No significant drift detected across all columns.",
            "likely_cause": "Data distribution is stable.",
        }

    # -------------------------------
    # 🔒 LLM SAFETY LAYER
    # -------------------------------
    if not explanation or not isinstance(explanation, dict):
        explanation = {
            "severity": "UNKNOWN",
            "summary": "LLM response invalid — fallback applied.",
            "likely_cause": "Parsing failure",
        }

    if not explanation.get("summary"):
        explanation["summary"] = "Significant data drift detected across one or more columns."

    if not explanation.get("likely_cause"):
        explanation["likely_cause"] = "Unable to determine exact cause (fallback applied)."

    # -------------------------------
    # 📊 Rule-based severity override
    # -------------------------------
    drift_rate = metrics["share_of_drifted_columns"]

    if drift_rate >= 0.5:
        explanation["severity"] = "HIGH"
    elif drift_rate >= 0.2:
        explanation["severity"] = "MEDIUM"
    else:
        explanation["severity"] = "LOW"

    # -------------------------------
    # 💾 Save to DB
    # -------------------------------
    summary = explanation.get("summary", "No explanation available")

    report_id = save_report(
        pipeline=pipeline_name,
        drift_rate=drift_rate,
        severity=explanation.get("severity", "UNKNOWN"),
        metrics=metrics,
        explanation=summary,
    )

    # -------------------------------
    # 🚨 Trigger Alert
    # -------------------------------
    trigger_alert(
        pipeline_name,
        explanation["severity"],
        drift_rate,
    )

    # -------------------------------
    # 📤 Response
    # -------------------------------
    return {
        "report_id": report_id,
        "pipeline": pipeline_name,
        "drift_rate": f"{drift_rate * 100:.1f}%",
        "metrics": metrics,
        "explanation": explanation,
        "warnings": warnings,
    }


# -------------------------------
# History Endpoint
# -------------------------------
@app.get("/history")
def get_history():
    return get_all_reports()


# -------------------------------
# Dashboard Endpoint
# -------------------------------
@app.get("/dashboard")
def dashboard():
    return get_dashboard_stats()


# -------------------------------
# Health Check
# -------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "DataDrift Analyzer"}


# -------------------------------
# Run Server
# -------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)