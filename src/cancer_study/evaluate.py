from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             confusion_matrix, roc_auc_score, roc_curve)

from .common import digest, fingerprint, read_json, write_json
from .datasets import model_inputs


def wilson(successes: int, total: int) -> list[float]:
    if total <= 0:
        raise ValueError("A binomial interval requires a nonzero denominator.")
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, float(center - half)), min(1.0, float(center + half))]


def metrics(y, probability, threshold: float) -> dict:
    y = np.asarray(y, dtype=int)
    probability = np.asarray(probability, dtype=float)
    predicted = (probability >= threshold).astype(int)
    tn, fp, fn, tp = [int(v) for v in confusion_matrix(y, predicted, labels=[0, 1]).ravel()]
    return {
        "n": len(y), "positive_class": "Malignant = 1", "threshold": float(threshold),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        "accuracy": float(accuracy_score(y, predicted)),
        "sensitivity": tp / (tp + fn), "specificity": tn / (tn + fp),
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "roc_auc": float(roc_auc_score(y, probability)),
        "average_precision": float(average_precision_score(y, probability)),
        "brier_score": float(brier_score_loss(y, probability)),
        "sensitivity_wilson_95": wilson(tp, tp + fn),
        "specificity_wilson_95": wilson(tn, tn + fp),
    }


def choose_threshold(y, probability, target: float) -> float:
    fpr, tpr, thresholds = roc_curve(y, probability, drop_intermediate=False)
    possible = [(float(1 - f), float(t)) for f, s, t in zip(fpr, tpr, thresholds)
                if s >= target and np.isfinite(t)]
    if not possible:
        raise ValueError("No finite threshold satisfies the declared development target.")
    return max(possible)[1]


def evaluate_once(project: Path, holdout: pd.DataFrame) -> dict:
    directory = project / "reports/metrics"
    freeze = read_json(directory / "freeze.json")
    model_path = project / "reports/model.joblib"
    if digest(model_path) != freeze["model_sha256"]:
        raise RuntimeError("Frozen model artifact changed.")
    identity = fingerprint({"freeze": digest(directory / "freeze.json"),
                            "holdout_ids": holdout.sample_id.tolist(),
                            "source": digest(project / "data/raw/wdbc.data"),
                            "evaluator": digest(Path(__file__))})
    lock_path = directory / "evaluation-lock.json"
    if lock_path.exists():
        lock = read_json(lock_path)
        if lock["identity"] != identity:
            raise RuntimeError("Final evaluation is locked to a different frozen study. Do not reuse the holdout to revise choices.")
        for relative, expected in lock["artifacts"].items():
            if not (project / relative).exists() or digest(project / relative) != expected:
                raise RuntimeError(f"Cached final evaluation artifact changed: {relative}")
        return read_json(directory / "holdout.json")
    model = joblib.load(model_path)
    x, y = model_inputs(holdout)
    probabilities = model.predict_proba(x)[:, list(model.classes_).index(1)]
    result = metrics(y, probabilities, freeze["threshold"])
    result.update({"model": freeze["model"], "partition": "holdout", "evaluation_identity": identity})
    predictions = holdout[["sample_id", "diagnosis", "target"]].copy()
    predictions["probability_malignant"] = probabilities
    predictions["predicted"] = (probabilities >= freeze["threshold"]).astype(int)
    predictions["correct"] = predictions.target == predictions.predicted
    predictions.to_csv(directory / "holdout_predictions.csv", index=False, float_format="%.17g")
    write_json(directory / "holdout.json", result)
    paths = ["reports/metrics/holdout.json", "reports/metrics/holdout_predictions.csv"]
    write_json(lock_path, {"identity": identity, "policy": "Reuse these results; no model or threshold revision using this holdout.",
                           "artifacts": {p: digest(project / p) for p in paths}})
    return result
