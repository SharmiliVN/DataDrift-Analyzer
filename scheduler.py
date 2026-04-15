# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from drift_engine import compute_drift
from llm_explainer import explain_drift
from db import save_report
from alert import trigger_alert

import pandas as pd


def run_scheduled_drift():
    """
    Simulated scheduled drift check.
    In production: replace with real data source (S3, DB, API)
    """

    print("\n⏱️ Running scheduled drift check...")

    try:
        # 🔹 For now: use sample CSVs
        ref_df = pd.read_csv("sample_data/reference.csv")
        cur_df = pd.read_csv("sample_data/current.csv")

        pipeline_name = "SCHEDULED-PIPELINE"

        # Step 1 — Compute drift
        metrics = compute_drift(ref_df, cur_df)

        # Step 2 — LLM explanation
        if metrics['number_of_drifted_columns'] > 0:
            explanation = explain_drift(metrics, pipeline_name)
        else:
            explanation = {
                'severity': 'LOW',
                'summary': 'No significant drift detected.',
                'likely_cause': 'Stable data'
            }

        # Step 3 — Rule override
        drift_rate = metrics['share_of_drifted_columns']

        if drift_rate >= 0.5:
            explanation['severity'] = 'HIGH'
        elif drift_rate >= 0.2:
            explanation['severity'] = 'MEDIUM'
        else:
            explanation['severity'] = 'LOW'

        # Step 4 — Save
        save_report(
            pipeline=pipeline_name,
            drift_rate=drift_rate,
            severity=explanation['severity'],
            metrics=metrics,
            explanation=explanation['summary']
        )

        # Step 5 — Alert
        trigger_alert(pipeline_name, explanation['severity'], drift_rate)

        print("✅ Scheduled drift check completed\n")

    except Exception as e:
        print("❌ Scheduler error:", e)


def start_scheduler():
    scheduler = BackgroundScheduler()

    # ⏱️ Runs every 2 minutes (change if needed)
    scheduler.add_job(run_scheduled_drift, "interval", minutes=2)

    scheduler.start()
    print("🚀 Scheduler started (runs every 2 minutes)")