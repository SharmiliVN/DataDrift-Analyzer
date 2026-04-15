# Purpose: PostgreSQL connection and drift report persistence
# Why psycopg2: battle-tested PostgreSQL driver, used in production systems

import psycopg2
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # loads .env file into environment

def get_connection():
    """
    Creates a fresh PostgreSQL connection.
    Why not a connection pool? For a portfolio project, fresh connections
    are simpler. In production you would use asyncpg + connection pooling.
    """
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    """
    Creates drift_reports table on startup if it does not exist.
    Called once when FastAPI app starts (see main.py lifespan).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS drift_reports (
            id          SERIAL PRIMARY KEY,
            pipeline    TEXT NOT NULL,
            report_date TIMESTAMP DEFAULT NOW(),
            drift_rate  FLOAT,
            severity    TEXT,
            metrics     JSONB,
            explanation TEXT
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def save_report(pipeline: str, drift_rate: float, severity: str,
                metrics: dict, explanation: str) -> int:
    """
    Persists one drift report. Returns the new report ID.
    JSONB type (not JSON) enables Postgres indexing on metrics later.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''INSERT INTO drift_reports
           (pipeline, drift_rate, severity, metrics, explanation)
           VALUES (%s, %s, %s, %s, %s) RETURNING id''',
        (pipeline, drift_rate, severity, json.dumps(metrics), explanation)
    )
    report_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return report_id

def get_all_reports():
    """
    Fetches all stored drift reports for the /history endpoint.
    Returns list of dicts so FastAPI can serialize to JSON easily.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, pipeline, report_date, drift_rate, severity, explanation FROM drift_reports ORDER BY report_date DESC')
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [
        {'id':r[0],'pipeline':r[1],'date':str(r[2]),'drift_rate':r[3],'severity':r[4],'explanation':r[5]}
        for r in rows
    ]

def get_dashboard_stats():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(drift_rate),
            SUM(CASE WHEN severity='HIGH' THEN 1 ELSE 0 END),
            SUM(CASE WHEN severity='MEDIUM' THEN 1 ELSE 0 END),
            SUM(CASE WHEN severity='LOW' THEN 1 ELSE 0 END)
        FROM drift_reports
    """)

    row = cur.fetchone()

    cur.execute("""
        SELECT pipeline
        FROM drift_reports
        GROUP BY pipeline
        ORDER BY MAX(report_date) DESC
        LIMIT 5
    """)

    pipelines = [r[0] for r in cur.fetchall()]

    cur.close()
    conn.close()

    return {
        "total_reports": row[0] or 0,
        "avg_drift_rate": round(float(row[1] or 0), 2),
        "high_severity": row[2] or 0,
        "medium_severity": row[3] or 0,
        "low_severity": row[4] or 0,
        "recent_pipelines": pipelines
    }