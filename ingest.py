# Purpose: Load two CSV snapshots and validate schema compatibility
# Why validate here: garbage in = garbage drift metrics.
#   Better to return a clear error than a meaningless drift report.

import pandas as pd
from io import BytesIO
from fastapi import HTTPException

def load_dataframes(ref_bytes: bytes, cur_bytes: bytes):
    """
    Loads reference and current CSVs into Pandas DataFrames.
    Performs schema compatibility check.

    Args:
        ref_bytes: raw bytes of the reference (baseline) CSV
        cur_bytes: raw bytes of the current (new batch) CSV

    Returns:
        (reference_df, current_df) tuple

    Raises:
        HTTPException 400 if schema mismatch or empty data
    """
    try:
        ref_df = pd.read_csv(BytesIO(ref_bytes))
        cur_df = pd.read_csv(BytesIO(cur_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'CSV parse error: {e}')

    # Validate non-empty
    if ref_df.empty or cur_df.empty:
        raise HTTPException(status_code=400, detail='One or both CSVs are empty')

    # Validate column compatibility
    ref_cols = set(ref_df.columns)
    cur_cols = set(cur_df.columns)

    missing_in_current = ref_cols - cur_cols
    new_in_current = cur_cols - ref_cols

    warnings = []
    if missing_in_current:
        warnings.append(f'Columns in reference but missing in current: {missing_in_current}')
    if new_in_current:
        warnings.append(f'New columns in current not in reference: {new_in_current}')

    # Keep only common columns for drift analysis
    common_cols = list(ref_cols & cur_cols)
    if not common_cols:
        raise HTTPException(status_code=400, detail='No common columns between reference and current')

    return ref_df[common_cols], cur_df[common_cols], warnings
