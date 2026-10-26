from pathlib import Path
import shutil
import numpy as np
import pandas as pd
import pytest

from cancer_study.common import read_json, root
from cancer_study.datasets import model_inputs
from cancer_study.evaluate import choose_threshold, evaluate_once, metrics, wilson
from cancer_study.ingest import COLUMNS, FEATURES, DataQualityError, acquire, validate_frame
from cancer_study.train import candidates, select_model


@pytest.fixture
def frame():
    rows = np.arange(4 * 30).reshape(4, 30) / 10
    result = pd.DataFrame(rows, columns=FEATURES)
    result.insert(0, "diagnosis", ["B", "M", "B", "M"])
    result.insert(0, "sample_id", ["10", "11", "12", "13"])
    return result


def test_zero_values_are_retained(frame):
    assert validate_frame(frame)["zero_measurements"] == 1


@pytest.mark.parametrize("fault", ["label", "missing", "infinite", "negative", "duplicate_id", "duplicate_features", "schema", "text"])
def test_bad_sources_fail_loudly(frame, fault):
    if fault == "label": frame.loc[0, "diagnosis"] = "unknown"
    if fault == "missing": frame.loc[0, FEATURES[0]] = np.nan
    if fault == "infinite": frame.loc[0, FEATURES[0]] = np.inf
    if fault == "negative": frame.loc[0, FEATURES[0]] = -1
    if fault == "duplicate_id": frame.loc[0, "sample_id"] = frame.loc[1, "sample_id"]
    if fault == "duplicate_features": frame.loc[0, FEATURES] = frame.loc[1, FEATURES]
    if fault == "schema": frame = frame.drop(columns=FEATURES[0])
    if fault == "text":
        frame[FEATURES[0]] = frame[FEATURES[0]].astype(object)
        frame.loc[0, FEATURES[0]] = "bad"
    with pytest.raises(DataQualityError): validate_frame(frame)


def test_model_input_whitelist_and_positive_label(frame):
    frame["target"] = frame.diagnosis.map({"B": 0, "M": 1})
    frame["partition"] = "development"
    x, y = model_inputs(frame)
    assert x.columns.tolist() == FEATURES
    assert y.tolist() == [0, 1, 0, 1]


def test_threshold_rule_and_inclusive_boundary():
    y, p = [0, 0, 1, 1], [.1, .6, .6, .9]
    threshold = choose_threshold(y, p, 1.0)
    assert threshold == .6
    result = metrics(y, p, threshold)
    assert (result["tp"], result["tn"], result["fp"], result["fn"]) == (2, 1, 1, 0)


def test_wilson_handles_boundary_counts():
    low, high = wilson(0, 10)
    assert low == 0 and .27 < high < .29
    low, high = wilson(10, 10)
    assert .71 < low < .73 and high == pytest.approx(1.0)
    with pytest.raises(ValueError): wilson(0, 0)


def test_simplicity_rule_with_practical_equivalence():
    protocol = read_json(root() / "protocol.json")
    table = pd.DataFrame({"model": protocol["simplicity_order"], "roc_auc": [.990, .994, .992]})
    assert select_model(table, protocol) == "Logistic regression"
    table.loc[1, "roc_auc"] = .999
    assert select_model(table, protocol) == "Calibrated RBF SVM"


def test_scaler_is_inside_calibration_and_validation_boundary():
    protocol = read_json(root() / "protocol.json")
    model = candidates(protocol)["Logistic regression"]
    x = pd.DataFrame({"measurement": [0., 1., 2., 3.]})
    model.fit(x, [0, 1, 0, 1])
    assert model.named_steps["standardscaler"].mean_[0] == 1.5
    model.predict(pd.DataFrame({"measurement": [10000.]}))
    assert model.named_steps["standardscaler"].mean_[0] == 1.5
    svm = candidates(protocol)["Calibrated RBF SVM"]
    assert "standardscaler" in svm.estimator.named_steps


def test_published_partitions_and_final_metrics_agree():
    project = root()
    source = pd.read_parquet(project / "data/processed/partitioned.parquet")
    development = set(source.loc[source.partition == "development", "sample_id"])
    holdout = set(source.loc[source.partition == "holdout", "sample_id"])
    assert not development & holdout
    assert len(development | holdout) == 569
    assert not source.duplicated(FEATURES).any()
    cv = pd.read_csv(project / "reports/metrics/development_predictions.csv", dtype={"sample_id": str})
    assert set(cv.sample_id) == development
    for _, group in cv.groupby("model"):
        assert len(group) == len(development) and group.sample_id.is_unique
        assert set(group.fold) == {1, 2, 3, 4, 5}
    predictions = pd.read_csv(project / "reports/metrics/holdout_predictions.csv", dtype={"sample_id": str}, float_precision="round_trip")
    final = read_json(project / "reports/metrics/holdout.json")
    assert set(predictions.sample_id) == holdout
    actual = metrics(predictions.target, predictions.probability_malignant, final["threshold"])
    for name in ["tp", "tn", "fp", "fn", "accuracy", "sensitivity", "specificity", "roc_auc", "brier_score"]:
        assert actual[name] == pytest.approx(final[name], abs=1e-12)
    assert sum(final[k] for k in ["tp", "tn", "fp", "fn"]) == final["n"] == len(holdout)


def test_changed_source_bytes_are_rejected(tmp_path):
    project = root()
    for relative in ["data/raw/wdbc.data", "data/source.json"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project / relative, target)
    with (tmp_path / "data/raw/wdbc.data").open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(DataQualityError, match="checksum changed"):
        acquire(tmp_path)


def test_changed_final_predictions_are_rejected(tmp_path):
    project = root()
    for relative in ["reports/metrics/freeze.json", "reports/metrics/evaluation-lock.json", "reports/metrics/holdout.json",
                     "reports/metrics/holdout_predictions.csv", "reports/model.joblib", "data/raw/wdbc.data"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project / relative, target)
    data = pd.read_parquet(project / "data/processed/partitioned.parquet")
    holdout = data.loc[data.partition == "holdout"].reset_index(drop=True)
    assert evaluate_once(tmp_path, holdout)["n"] == len(holdout)
    with (tmp_path / "reports/metrics/holdout_predictions.csv").open("a") as stream:
        stream.write("\n")
    with pytest.raises(RuntimeError, match="artifact changed"):
        evaluate_once(tmp_path, holdout)
