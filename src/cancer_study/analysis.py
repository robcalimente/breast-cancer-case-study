from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def sql_summaries(project: Path, frame: pd.DataFrame) -> None:
    with duckdb.connect() as connection:
        connection.register("samples", frame)
        for name in ["cohort_summary", "feature_summary"]:
            result = connection.execute((project / f"sql/{name}.sql").read_text()).df()
            result.to_csv(project / f"reports/metrics/{name}.csv", index=False)


def descriptive_results(development: pd.DataFrame) -> dict:
    columns = ["radius_mean", "texture_mean", "concave_points_worst"]
    medians = development.groupby("diagnosis")[columns].median()
    return {"medians": medians.to_dict(),
            "radius_perimeter_correlation": float(development.radius_mean.corr(development.perimeter_mean)),
            "radius_area_correlation": float(development.radius_mean.corr(development.area_mean)),
            "development_rows": len(development)}
