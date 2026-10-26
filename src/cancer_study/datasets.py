from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from .common import read_json
from .ingest import FEATURES, DataQualityError


def assign_splits(project: Path, frame: pd.DataFrame) -> pd.DataFrame:
    protocol = read_json(project / "protocol.json")
    path = project / "data/processed/splits.csv"
    development, holdout = train_test_split(
        frame.sample_id, test_size=protocol["holdout_fraction"],
        stratify=frame.target, random_state=protocol["seed"],
    )
    expected = pd.DataFrame({"sample_id": frame.sample_id,
                             "partition": frame.sample_id.map({**dict.fromkeys(development, "development"),
                                                                  **dict.fromkeys(holdout, "holdout")})})
    if path.exists():
        saved = pd.read_csv(path, dtype={"sample_id": str})
        if not saved.equals(expected.reset_index(drop=True)):
            raise DataQualityError("Saved split assignments disagree with the source or protocol. Do not silently resplit.")
    else:
        expected.to_csv(path, index=False)
    joined = frame.merge(expected, on="sample_id", validate="one_to_one")
    joined.to_parquet(project / "data/processed/partitioned.parquet", index=False)
    joined.loc[joined.partition == "development"].to_parquet(project / "data/processed/development.parquet", index=False)
    return joined


def model_inputs(frame: pd.DataFrame):
    """Explicit whitelist prevents IDs, labels, and partition metadata becoming predictors."""
    return frame.loc[:, FEATURES], frame.target


def load_development(project: Path) -> pd.DataFrame:
    return pd.read_parquet(project / "data/processed/development.parquet")
