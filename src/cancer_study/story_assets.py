"""Editorial figures drawn from the frozen evaluation, without fitting a model."""
from __future__ import annotations

import csv
from html import escape
from math import ceil
from pathlib import Path


def write_outcome_maps(project: Path) -> None:
    with (project / "reports/metrics/holdout_predictions.csv").open() as stream:
        samples = list(csv.DictReader(stream))
    correct = sum(row["correct"] == "True" for row in samples)
    errors = len(samples) - correct
    for columns, name in [(19, "holdout-outcomes.svg"), (12, "holdout-outcomes-mobile.svg")]:
        gap_x, gap_y, padding = 42, 34, 16
        width = 2 * padding + (columns - 1) * gap_x
        height = 2 * padding + (ceil(len(samples) / columns) - 1) * gap_y
        elements = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="outcomes-title outcomes-description">',
                    f'<title id="outcomes-title">{correct} correct classifications and {errors} errors across {len(samples)} holdout samples</title>',
                    '<desc id="outcomes-description">One marker per held-out breast-mass sample, in source row order. Filled blue-green dots mark correct classifications. Rust rings mark malignant samples classified as benign.</desc>']
        for index, sample in enumerate(samples):
            x = padding + index % columns * gap_x
            y = padding + index // columns * gap_y
            outcome = "correct" if sample["correct"] == "True" else "missed-malignant"
            if outcome != "correct" and not (sample["target"] == "1" and sample["predicted"] == "0"):
                raise ValueError("Update the outcome-map legend for a different error type.")
            elements.append(f'<g data-sample-id="{escape(sample["sample_id"])}" data-outcome="{outcome}">')
            elements.append(f'<title>Sample {escape(sample["sample_id"])}: {outcome}; estimated malignant probability {float(sample["probability_malignant"]):.4f}</title>')
            if outcome == "correct":
                elements.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#467e85"/>')
            else:
                elements.append(f'<circle cx="{x}" cy="{y}" r="11" fill="none" stroke="#b94e41" stroke-width="2.5"/>')
                elements.append(f'<circle cx="{x}" cy="{y}" r="3" fill="#b94e41"/>')
            elements.append('</g>')
        elements.append('</svg>')
        (project / "site/assets" / name).write_text("\n".join(elements) + "\n")
