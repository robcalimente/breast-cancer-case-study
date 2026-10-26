"""Refit the development experiment in a temporary workspace, never evaluating the holdout."""
from pathlib import Path
import shutil
import tempfile

import numpy as np
import pandas as pd

from cancer_study.common import read_json
from cancer_study.train import train

project = Path(__file__).resolve().parents[1]
published = read_json(project / "reports/metrics/freeze.json")
with tempfile.TemporaryDirectory(prefix="sample-signal-development-") as temp:
    work = Path(temp)
    inputs = [*published["training_identity"]["files"], "data/processed/development.parquet"]
    for relative in inputs:
        target = work / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project / relative, target)
    development = pd.read_parquet(work / "data/processed/development.parquet")
    result = train(work, development)
    assert result["model"] == published["model"], "Selected candidate changed."
    assert np.isclose(result["threshold"], published["threshold"], rtol=1e-8, atol=1e-9), "Development threshold changed."
    for name, columns in [("cross_validation.csv", ["roc_auc"]), ("development_predictions.csv", ["probability_malignant"])]:
        expected = pd.read_csv(project / "reports/metrics" / name)
        actual = pd.read_csv(work / "reports/metrics" / name)
        assert expected.shape == actual.shape
        for column in columns:
            assert np.allclose(expected[column], actual[column], rtol=1e-8, atol=1e-9), f"{name}: {column} changed."
    print("Fresh development refit agrees with the published candidate, threshold, and prediction artifacts.")
    print("No holdout observations were loaded or evaluated.")
