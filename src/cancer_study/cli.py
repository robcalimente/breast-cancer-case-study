from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
from pathlib import Path
import platform
import subprocess

from .analysis import descriptive_results, sql_summaries
from .common import digest, read_json, root, write_json
from .datasets import assign_splits
from .evaluate import evaluate_once
from .ingest import ingest
from .train import train


def pipeline(project: Path) -> dict:
    print("Validating source and persisted split…", flush=True)
    frame, quality = ingest(project)
    partitioned = assign_splits(project, frame)
    development = partitioned.loc[partitioned.partition == "development"].reset_index(drop=True)
    holdout = partitioned.loc[partitioned.partition == "holdout"].reset_index(drop=True)
    sql_summaries(project, partitioned)
    write_json(project / "reports/metrics/exploration.json", descriptive_results(development))
    freeze = train(project, development)
    print(f"Frozen model: {freeze['model']}; threshold: {freeze['threshold']:.6f}", flush=True)
    final = evaluate_once(project, holdout)
    from .plots import render_figures
    from .publish import build_report_sources
    render_figures(project, development, final)
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project, stderr=subprocess.DEVNULL, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=project, text=True).strip())
    except subprocess.CalledProcessError:
        revision, dirty = None, True
    tracked = [*project.glob("src/cancer_study/*.py"), project / "protocol.json", project / "uv.lock",
               *project.glob("sql/*.sql"), *project.glob("data/processed/*"), *project.glob("reports/metrics/*")]
    write_json(project / "reports/manifests/run.json", {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "code_revision": revision,
        "working_tree_has_changes": dirty,
        "source_sha256": digest(project / "data/raw/wdbc.data"),
        "training_fingerprint": freeze["training_fingerprint"],
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name) for name in ["pandas", "numpy", "scikit-learn", "duckdb", "pyarrow", "matplotlib"]},
        "artifacts": {str(p.relative_to(project)): digest(p) for p in sorted(tracked)},
    })
    build_report_sources(project, quality, development, final)
    print(f"Final holdout: {final['tp']} TP, {final['tn']} TN, {final['fp']} FP, {final['fn']} FN; n={final['n']}", flush=True)
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce From Sample to Signal.")
    parser.add_argument("command", choices=["run", "data"])
    args = parser.parse_args()
    project = root()
    if args.command == "data":
        frame, _ = ingest(project)
        assign_splits(project, frame)
        print("Source validated and split assignments persisted.")
    else:
        pipeline(project)


if __name__ == "__main__":
    main()
