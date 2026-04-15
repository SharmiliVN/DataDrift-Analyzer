# alerts.py

def trigger_alert(pipeline: str, severity: str, drift_rate: float):
    """
    Simple alert mechanism.
    In production: replace with Slack / email / PagerDuty
    """

    if severity == "HIGH":
        print("\n🚨 HIGH DRIFT ALERT 🚨")
        print(f"Pipeline: {pipeline}")
        print(f"Drift Rate: {drift_rate*100:.1f}%")
        print("Action: Investigate immediately\n")