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
        if "model" in expected:
            assert expected["model"].equals(actual["model"]), f"{name}: model row order changed."
        for key in ["sample_id", "target", "fold"]:
            if key in expected:
                assert expected[key].equals(actual[key]), f"{name}: {key} changed."
        for column in columns:
            delta = np.abs(expected[column] - actual[column])
            for model in expected["model"].unique():
                mask = expected["model"] == model
                print(f"{name}: {model}: max absolute {column} difference = {delta[mask].max():.12g}", flush=True)
                # The frozen artifacts remain byte-checked by the main pipeline.
                # A fresh Linux forest differs from the original Mac refit by up to
                # 0.003612 probability; its fold AUCs and 0.5 decisions agree.
                # Bound that unselected comparison candidate separately. Preserve
                # strict checks for the selected model, threshold, and all AUCs.
                forest_probability = model == "Random forest" and column == "probability_malignant"
                atol = 0.005 if forest_probability else 1e-9
                assert np.allclose(expected.loc[mask, column], actual.loc[mask, column], rtol=1e-8, atol=atol), f"{name}: {model}: {column} changed beyond {atol}; max absolute difference {delta[mask].max():.12g}."
                if column == "probability_malignant":
                    threshold = published["threshold"] if model == published["model"] else 0.5
                    assert np.array_equal(expected.loc[mask, column] >= threshold, actual.loc[mask, column] >= threshold), f"{model}: development classifications changed."
    print("Fresh development refit agrees with the published candidate, threshold, fold AUCs, and classifications within documented probability tolerances.")
    print("No holdout observations were loaded or evaluated.")
