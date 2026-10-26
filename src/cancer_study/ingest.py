from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd

from .common import digest, read_json, write_json

BASE_FEATURES = ["radius", "texture", "perimeter", "area", "smoothness", "compactness",
                 "concavity", "concave_points", "symmetry", "fractal_dimension"]
FEATURES = [f"{name}_{summary}" for summary in ["mean", "se", "worst"] for name in BASE_FEATURES]
COLUMNS = ["sample_id", "diagnosis", *FEATURES]
SOURCE_URL = "https://archive.ics.uci.edu/static/public/17/breast+cancer+wisconsin+diagnostic.zip"


class DataQualityError(ValueError):
    pass


def acquire(project: Path) -> Path:
    """Fetch once; validate all later runs against the accepted snapshot manifest."""
    import io
    import zipfile

    raw = project / "data/raw/wdbc.data"
    manifest = project / "data/source.json"
    if not raw.exists():
        if manifest.exists():
            # Download the exact documented source; the checksum below still has to match.
            source_url = read_json(manifest)["url"]
        else:
            source_url = SOURCE_URL
        with urlopen(source_url, timeout=60) as response:
            archive = response.read()
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(zipped.read("wdbc.data"))
            (raw.parent / "wdbc.names").write_bytes(zipped.read("wdbc.names"))
        if not manifest.exists():
            write_json(manifest, {
                "url": source_url, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": digest(raw), "license": "CC BY 4.0",
                "citation": "Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1993). Breast Cancer Wisconsin (Diagnostic). UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B",
                "file": "data/raw/wdbc.data", "observation_unit": "one breast-mass sample",
            })
    if not manifest.exists():
        raise DataQualityError("Source exists without an accepted data/source.json manifest.")
    if digest(raw) != read_json(manifest)["sha256"]:
        raise DataQualityError("Source checksum changed. Investigate rather than silently accepting a new snapshot.")
    return raw


def validate_frame(frame: pd.DataFrame) -> dict:
    """Strict schema and domain checks; no silent repairs or row removal."""
    if list(frame.columns) != COLUMNS:
        raise DataQualityError(f"Expected exactly {len(COLUMNS)} named columns in source order.")
    if frame.empty:
        raise DataQualityError("Source contains no observations.")
    if frame.isna().any().any():
        raise DataQualityError("Missing values detected.")
    if not frame.diagnosis.isin(["B", "M"]).all():
        raise DataQualityError("Diagnosis must be B or M.")
    if set(frame.diagnosis) != {"B", "M"}:
        raise DataQualityError("Both diagnosis classes must be present.")
    identifiers = frame.sample_id.astype(str)
    if not identifiers.str.fullmatch(r"\d+").all() or identifiers.duplicated().any():
        raise DataQualityError("Sample identifiers must be unique strings of digits.")
    try:
        values = frame[FEATURES].to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise DataQualityError("Measurements must be numeric.") from exc
    if not np.isfinite(values).all():
        raise DataQualityError("Non-finite measurement detected.")
    if (values < 0).any():
        raise DataQualityError("Negative measurement detected; all source features are nonnegative.")
    duplicates = int(frame.duplicated(subset=FEATURES, keep=False).sum())
    if duplicates:
        raise DataQualityError("Duplicate feature vectors require grouping or source review before splitting.")
    return {
        "status": "passed", "rows": len(frame), "measurement_columns": len(FEATURES),
        "missing_values": 0, "duplicate_identifiers": 0, "duplicate_feature_vectors": 0,
        "nonfinite_values": 0, "negative_measurements": 0,
        "benign": int((frame.diagnosis == "B").sum()),
        "malignant": int((frame.diagnosis == "M").sum()),
        "zero_measurements": int((values == 0).sum()),
        "checks": ["column count and order", "nonempty source", "complete values", "valid labels",
                   "both classes present", "unique numeric identifiers", "numeric finite measurements",
                   "nonnegative measurements", "no duplicate feature vectors"],
    }


def ingest(project: Path) -> tuple[pd.DataFrame, dict]:
    raw = acquire(project)
    # Read headers separately so an extra source field cannot be silently treated as an index.
    frame = pd.read_csv(raw, header=None, dtype={0: str})
    if frame.shape[1] != len(COLUMNS):
        raise DataQualityError(f"Source has {frame.shape[1]} columns; expected {len(COLUMNS)}.")
    frame.columns = COLUMNS
    quality = validate_frame(frame)
    frame[FEATURES] = frame[FEATURES].astype(float)
    frame["target"] = frame.diagnosis.map({"B": 0, "M": 1}).astype(int)
    destination = project / "data/processed"
    destination.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(destination / "samples.parquet", index=False)
    write_json(project / "reports/metrics/quality.json", quality)
    return frame, quality
