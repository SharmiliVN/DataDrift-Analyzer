# 🚀 DataDrift Analyzer  
LLM-Powered Data Drift Detection for Tabular Pipelines  

Upload two CSV snapshots → detect drift → get a plain-English explanation → store history.

---

## 🧠 Why This Project Exists

Modern data pipelines fail silently.

- A vendor changes format → no error  
- A column becomes null → pipeline still runs  
- Market behavior shifts → model degrades  

By the time someone notices, damage is already done.

This tool catches those issues as they happen.

---

## 💡 What Makes This Different

Most tools (like Evidently) give you numbers:

PSI = 0.42

This project adds an LLM reasoning layer that explains:

"trade_volume increased by 312% — likely upstream feed change or market anomaly."

---

## ⚙️ Key Features

### 🔍 Automated Drift Detection
- Uses Evidently AI
- Detects:
  - Distribution shifts
  - Mean changes
  - Null spikes
  - Schema inconsistencies

### 🧠 LLM-Powered Explanation
- Converts raw metrics into human-readable insights
- Outputs:
  - Severity (LOW / MEDIUM / HIGH)
  - Summary
  - Likely root cause

### 🗄️ Drift History Tracking
- Stores reports in PostgreSQL
- Enables:
  - Audit trails
  - Trend analysis

### ⚡ FastAPI Backend
- REST API with Swagger docs
- Test easily via /docs

---

## 🏗️ Architecture Overview

User → Upload CSVs  
↓  
FastAPI (/analyze)  
↓  
Ingestion (Pandas)  
↓  
Drift Engine (Evidently)  
↓  
LLM Explainer (GPT)  
↓  
PostgreSQL Storage  
↓  
JSON Response  

---

## 🛠️ Tech Stack

- Python  
- FastAPI + Uvicorn  
- Evidently AI  
- OpenAI / Claude API  
- PostgreSQL  
- Pandas, NumPy, SciPy  

---

## 🚀 Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/datadrift-analyzer
cd datadrift-analyzer

pip install -r requirements.txt

cp .env.example .env
# add your API key and DB URL

python main.py

Open: http://localhost:8000/docs

📡 API Endpoints

POST /analyze

Upload:

Reference CSV
Current CSV

Returns:

Drift metrics
LLM explanation
Severity
GET /history

View all past drift reports

GET /health

Service health check

🧪 Example

Input
Reference CSV:

trade_volume,rate
1000,83.5
1200,83.6

Current CSV:
trade_volume,rate
10500,84.1
9800,83.9

Output
{
  "severity": "HIGH",
  "summary": "trade_volume shows significant increase",
  "likely_cause": "market anomaly or upstream feed change"
}


🎯 Real-World Inspiration

Inspired by real production issues during financial pipeline development at 3Cortex, where silent upstream failures caused data inconsistencies.

🧠 Key Engineering Decisions

Used Evidently for reliable statistical metrics
Added LLM layer for interpretation
Stored results for audit and debugging
Sent only drifted columns to LLM (optimized cost)


🔮 Future Improvements
Async DB (asyncpg)
Authentication (JWT)
Alert system (Slack / Email)
Scheduled drift monitoring
Frontend dashboard


📁 Project Structure
datadrift-analyzer/
├── main.py
├── ingest.py
├── drift_engine.py
├── llm_explainer.py
├── db.py
├── requirements.txt
├── .env.example
├── README.md
