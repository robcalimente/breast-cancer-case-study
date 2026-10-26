from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .common import digest, fingerprint, read_json, write_json
from .datasets import model_inputs
from .evaluate import choose_threshold, metrics


def candidates(protocol: dict) -> dict:
    seed = protocol["seed"]
    params = protocol["candidates"]
    svm = params["Calibrated RBF SVM"]
    calibration_cv = StratifiedKFold(n_splits=svm["calibration_folds"], shuffle=True, random_state=seed)
    return {
        "Majority baseline": DummyClassifier(strategy="prior"),
        "Logistic regression": make_pipeline(StandardScaler(), LogisticRegression(**params["Logistic regression"], random_state=seed)),
        "Calibrated RBF SVM": CalibratedClassifierCV(
            make_pipeline(StandardScaler(), SVC(C=svm["C"], gamma=svm["gamma"], random_state=seed)),
            method=svm["calibration"], cv=calibration_cv, ensemble=True),
        "Random forest": RandomForestClassifier(**params["Random forest"], random_state=seed, n_jobs=1),
    }


def select_model(comparison: pd.DataFrame, protocol: dict) -> str:
    means = comparison.groupby("model").roc_auc.mean()
    best = max(means.loc[name] for name in protocol["simplicity_order"])
    return next(name for name in protocol["simplicity_order"]
                if means.loc[name] >= best - protocol["practical_equivalence_auc"])


def training_identity(project: Path) -> dict:
    files = ["protocol.json", "uv.lock", "data/raw/wdbc.data", "data/processed/splits.csv",
             "src/cancer_study/train.py", "src/cancer_study/ingest.py", "src/cancer_study/datasets.py"]
    return {"files": {p: digest(project / p) for p in files}, "scikit_learn": sklearn.__version__}


def train(project: Path, development: pd.DataFrame) -> dict:
    protocol = read_json(project / "protocol.json")
    directory = project / "reports/metrics"
    directory.mkdir(parents=True, exist_ok=True)
    identity = training_identity(project)
    freeze_path = directory / "freeze.json"
    if freeze_path.exists():
        freeze = read_json(freeze_path)
        if freeze["training_identity"] != identity:
            raise RuntimeError("Training inputs changed after freezing. Keep the published study intact; a revised experiment needs new evaluation evidence.")
        for relative, expected in freeze["development_artifacts"].items():
            if not (project / relative).exists() or digest(project / relative) != expected:
                raise RuntimeError(f"Frozen development artifact changed: {relative}")
        if digest(project / "reports/model.joblib") != freeze["model_sha256"]:
            raise RuntimeError("Frozen model artifact changed.")
        return freeze
    registration = directory / "protocol-registration.json"
    if registration.exists() and read_json(registration)["protocol_sha256"] != digest(project / "protocol.json"):
        raise RuntimeError("The registered protocol changed.")
    if not registration.exists():
        write_json(registration, {"registered_at_utc": datetime.now(timezone.utc).isoformat(),
                                  "protocol_sha256": digest(project / "protocol.json"),
                                  "training_identity": identity})
    x, y = model_inputs(development)
    cv = StratifiedKFold(n_splits=protocol["development_folds"], shuffle=True, random_state=protocol["seed"])
    splits = list(cv.split(x, y))
    folds, predictions = [], []
    models = candidates(protocol)
    for name, estimator in models.items():
        print(f"  Cross-validating {name}…", flush=True)
        out_of_fold = np.zeros(len(x))
        fold_ids = np.zeros(len(x), dtype=int)
        for fold, (fit_idx, validate_idx) in enumerate(splits, start=1):
            model = clone(estimator).fit(x.iloc[fit_idx], y.iloc[fit_idx])
            p = model.predict_proba(x.iloc[validate_idx])[:, list(model.classes_).index(1)]
            out_of_fold[validate_idx] = p
            fold_ids[validate_idx] = fold
            folds.append({"model": name, "fold": fold, "n": len(validate_idx),
                          "roc_auc": float(roc_auc_score(y.iloc[validate_idx], p))})
        frame = development[["sample_id", "target"]].copy()
        frame["model"], frame["probability_malignant"], frame["fold"] = name, out_of_fold, fold_ids
        predictions.append(frame)
    comparison = pd.DataFrame(folds)
    comparison.to_csv(directory / "cross_validation.csv", index=False, float_format="%.17g")
    all_predictions = pd.concat(predictions, ignore_index=True)
    all_predictions.to_csv(directory / "development_predictions.csv", index=False, float_format="%.17g")
    selected = select_model(comparison, protocol)
    chosen = all_predictions.loc[all_predictions.model == selected]
    threshold = choose_threshold(chosen.target, chosen.probability_malignant, protocol["illustrative_sensitivity_target"])
    write_json(directory / "development.json", metrics(chosen.target, chosen.probability_malignant, threshold))
    model = clone(models[selected]).fit(x, y)
    model_path = project / "reports/model.joblib"
    joblib.dump(model, model_path)
    paths = ["reports/metrics/cross_validation.csv", "reports/metrics/development_predictions.csv", "reports/metrics/development.json"]
    freeze = {"model": selected, "threshold": threshold,
              "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
              "training_identity": identity, "training_fingerprint": fingerprint(identity),
              "model_sha256": digest(model_path),
              "development_artifacts": {p: digest(project / p) for p in paths},
              "note": "Model choice and threshold use development data only. OOF estimates are exploratory after selection, not unbiased final performance."}
    write_json(freeze_path, freeze)
    return freeze
