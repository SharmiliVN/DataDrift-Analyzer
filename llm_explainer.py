import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"   # or mistral / phi3 depending on what you installed


SYSTEM_PROMPT = """
You are a senior data engineer analyzing pipeline health.

Given drift statistics, produce a STRICT JSON response:

{
  "severity": "LOW|MEDIUM|HIGH",
  "summary": "Include column names AND numeric changes (%, shift, etc)",
  "likely_cause": "Specific cause like feed change, schema drift, market spike, etc"
}

Rules:
- Be specific (mention % change if available)
- Do NOT be generic
- Do NOT say 'some columns'
- Always mention column names
- Always explain WHY it might have happened
- Max 3 sentences
"""


def explain_drift(metrics: dict, pipeline_name: str) -> dict:

    drift_rate = metrics["share_of_drifted_columns"]
    drifted = metrics["drifted_columns"]

    prompt = f"""
{SYSTEM_PROMPT}

Pipeline: {pipeline_name}

Total columns: {metrics['total_columns']}
Drifted columns: {metrics['number_of_drifted_columns']}
Drift rate: {drift_rate * 100:.1f}%

Drifted column details:
{json.dumps(drifted, indent=2)}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
        )

        result = response.json()
        raw_text = result.get("response", "").strip()

        # 🔥 CLEAN RESPONSE
        clean = raw_text.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(clean)

            return {
                "severity": parsed.get("severity", "UNKNOWN"),
                "summary": parsed.get("summary", "No summary provided"),
                "likely_cause": parsed.get("likely_cause", "Unknown cause")
            }

        except json.JSONDecodeError:
            return {
                "severity": "UNKNOWN",
                "summary": clean,
                "likely_cause": "Ollama returned non-JSON response"
            }

    except Exception as e:
        return {
            "severity": "UNKNOWN",
            "summary": f"Ollama call failed: {str(e)}",
            "likely_cause": "Connection or model error"
        }