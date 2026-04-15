# Purpose: Compute drift metrics between reference and current DataFrames
# Why Evidently: 25k+ star open-source library used in production by
#   companies like Realtor.com, Wise, and DataTalks.Club.
#   It handles the statistical complexity (PSI, KS test, Wasserstein)
#   so we don't reinvent the wheel.

from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
import pandas as pd
import json

def compute_drift(ref_df: pd.DataFrame, cur_df: pd.DataFrame) -> dict:
    """
    Runs Evidently DataDriftPreset on reference vs current DataFrames.
    Extracts per-column drift stats into a clean dict.

    Returns a dict structured as:
    {
        "share_of_drifted_columns": float,   # 0.0 to 1.0
        "number_of_drifted_columns": int,
        "total_columns": int,
        "drifted_columns": [
            {
                "column": str,
                "stat_test": str,      # e.g. "PSI", "ks"
                "drift_score": float,  # higher = more drift
                "drifted": bool,
                "current_mean": float,
                "ref_mean": float,
                "mean_shift_pct": str
            },
            ...
        ]
    }
    """
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref_df, current_data=cur_df)

    # Evidently outputs to a dict — we extract the parts we need
    raw = report.as_dict()
    drift_result = raw['metrics'][0]['result']
    col_results  = raw['metrics'][1]['result']

    drifted_cols = []
    for col_name, stats in col_results['drift_by_columns'].items():
        entry = {
            'column':     col_name,
            'stat_test':  stats.get('stattest_name', 'unknown'),
            'drift_score': round(stats.get('drift_score', 0), 4),
            'drifted':    stats.get('drift_detected', False),
        }
        # Add mean shift for numeric columns if available
        ref_mean = stats.get('reference_distribution', {}).get('mean')
        cur_mean = stats.get('current_distribution',   {}).get('mean')
        if ref_mean is not None and cur_mean is not None and ref_mean != 0:
            shift_pct = ((cur_mean - ref_mean) / abs(ref_mean)) * 100
            entry['ref_mean']       = round(ref_mean, 4)
            entry['current_mean']   = round(cur_mean, 4)
            entry['mean_shift_pct'] = f'{shift_pct:+.1f}%'
        drifted_cols.append(entry)

    # Sort: drifted columns first, then by drift_score descending
    drifted_cols.sort(key=lambda x: (-x['drifted'], -x['drift_score']))

    return {
        'share_of_drifted_columns':  drift_result.get('share_of_drifted_columns', 0),
        'number_of_drifted_columns': drift_result.get('number_of_drifted_columns', 0),
        'total_columns':             drift_result.get('number_of_columns', 0),
        'drifted_columns': [c for c in drifted_cols if c['drifted']]
    }
