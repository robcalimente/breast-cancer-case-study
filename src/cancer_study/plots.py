from __future__ import annotations

from html import escape
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve

from .common import read_json
from .ingest import BASE_FEATURES

BENIGN, MALIGNANT, INK, MUTED, PAPER = "#217d80", "#c56636", "#252b33", "#59636f", "#ffffff"
LABELS = {"radius_mean": "Mean radius", "texture_mean": "Mean texture", "concave_points_worst": "Worst concave points"}


def style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.labelsize": 10,
        "axes.titlesize": 12, "axes.titleweight": "semibold", "text.color": INK,
        "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": "#d7dfd8", "axes.spines.top": False, "axes.spines.right": False,
        "axes.facecolor": PAPER, "figure.facecolor": PAPER, "savefig.facecolor": PAPER,
        "grid.color": "#e4e8e0", "svg.fonttype": "none", "svg.hashsalt": "sample-to-signal",
    })


def save(fig, path: Path, title: str, description: str) -> None:
    fig.savefig(path, bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)
    svg = path.read_text()
    svg = svg.replace("<svg ", '<svg role="img" aria-labelledby="chart-title chart-desc" ', 1)
    start = svg.index(">", svg.index("<svg")) + 1
    svg = svg[:start] + f'<title id="chart-title">{escape(title)}</title><desc id="chart-desc">{escape(description)}</desc>' + svg[start:]
    path.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n")


def render_figures(project: Path, development: pd.DataFrame, final: dict) -> None:
    style()
    assets = project / "site/assets"
    assets.mkdir(parents=True, exist_ok=True)
    colors = {"B": BENIGN, "M": MALIGNANT}
    fig, ax = plt.subplots(figsize=(7.2, 5.7))
    for label, marker in [("B", "o"), ("M", "^")]:
        rows = development.loc[development.diagnosis == label]
        ax.scatter(rows.radius_mean, rows.concave_points_worst, s=24, marker=marker,
                   c=colors[label], alpha=.70, edgecolors=PAPER, linewidths=.3,
                   label=f"{'Benign' if label == 'B' else 'Malignant'} · {len(rows)}")
    ax.set(xlabel="Mean radius · source scale", ylabel="Worst concave points · source scale")
    ax.grid(alpha=.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", fontsize=10)
    ax.text(.98, .03, f"Each mark is one sample\nDevelopment partition · n={len(development)}",
            transform=ax.transAxes, ha="right", color=MUTED, fontsize=9, linespacing=1.5)
    save(fig, assets / "sample-map.svg", "Cell measurements show separation and overlap",
         "Development samples plotted by mean radius and worst concave points. Benign samples are teal circles; malignant samples are amber triangles. These two measurements do not separate every sample.")

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    for ax, column in zip(axes, LABELS):
        for label in ["B", "M"]:
            values = development.loc[development.diagnosis == label, column]
            sns.kdeplot(values, ax=ax, color=colors[label], fill=True, alpha=.13,
                        linewidth=1.8, clip=(0, None), label="Benign" if label == "B" else "Malignant")
            ax.axvline(values.median(), color=colors[label], linestyle=":" if label == "B" else "--", alpha=.65)
        ax.set(title=LABELS[column], xlabel="Source scale", ylabel="Density")
        ax.grid(axis="y", alpha=.5)
    axes[0].legend(frameon=False, fontsize=9)
    fig.tight_layout(w_pad=2)
    save(fig, assets / "distributions.svg", "The classes differ, but their distributions overlap",
         "Smoothed development-set distributions for mean radius, mean texture, and worst concave points. Vertical lines mark class medians. Smoothing is descriptive and does not determine model inputs.")

    # A separate composition preserves labels on narrow screens.
    fig, axes = plt.subplots(3, 1, figsize=(4.5, 8.4))
    for ax, column in zip(axes, LABELS):
        for label in ["B", "M"]:
            values = development.loc[development.diagnosis == label, column]
            sns.kdeplot(values, ax=ax, color=colors[label], fill=True, alpha=.13,
                        linewidth=1.8, clip=(0, None), label="Benign" if label == "B" else "Malignant")
            ax.axvline(values.median(), color=colors[label], linestyle=":" if label == "B" else "--", alpha=.65)
        ax.set(title=LABELS[column], xlabel="Source scale", ylabel="Density")
        ax.grid(axis="y", alpha=.5)
    axes[0].legend(frameon=False, fontsize=9)
    fig.tight_layout(h_pad=2)
    save(fig, assets / "distributions-mobile.svg", "Class distributions, stacked for narrow screens",
         "The same three development distributions as the wide composition, arranged vertically to preserve readable labels.")

    columns = [f"{name}_mean" for name in BASE_FEATURES]
    labels = [name.replace("_", " ").capitalize() for name in BASE_FEATURES]
    fig, ax = plt.subplots(figsize=(8, 6.2))
    corr = development[columns].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), 1)
    sns.heatmap(corr, mask=mask, vmin=-1, vmax=1, center=0, cmap="BrBG", annot=True,
                fmt=".1f", annot_kws={"size": 8}, xticklabels=labels, yticklabels=labels,
                cbar_kws={"label": "Pearson correlation", "shrink": .7}, ax=ax, linewidths=.7)
    ax.tick_params(axis="both", length=0)
    plt.setp(ax.get_xticklabels(), rotation=50, ha="right", fontsize=8)
    plt.setp(ax.get_yticklabels(), fontsize=8)
    save(fig, assets / "correlations.svg", "Many measurements describe related properties",
         "Pearson correlations among the ten mean measurements on development data only. Radius, perimeter, and area are strongly related. Correlation does not establish causation.")

    cv = pd.read_csv(project / "reports/metrics/cross_validation.csv")
    order = ["Majority baseline", "Logistic regression", "Calibrated RBF SVM", "Random forest"]
    freeze = read_json(project / "reports/metrics/freeze.json")
    fig, ax = plt.subplots(figsize=(9, 3.6))
    for position, name in enumerate(order):
        scores = cv.loc[cv.model == name, "roc_auc"].to_numpy()
        color = BENIGN if name == freeze["model"] else MUTED
        ax.scatter(scores, position + np.linspace(-.10, .10, len(scores)), s=28, c=color, alpha=.6)
        ax.plot(scores.mean(), position, marker="D", color=color, markersize=7)
        ax.text(1.025, position, f"{scores.mean():.3f} ± {scores.std(ddof=1):.3f}", va="center", fontsize=9, color=INK)
    ax.set(yticks=range(len(order)), yticklabels=order, xlabel="Validation ROC-AUC", xlim=(.46, 1.02), ylim=(3.5, -.5))
    ax.grid(axis="x", alpha=.6)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=12)
    ax.text(1.025, -.65, "Mean ± fold SD", fontsize=8, color=MUTED)
    save(fig, assets / "model-comparison.svg", "A fair comparison includes a simple baseline",
         "Five validation-fold ROC-AUC results for each candidate. Small dots show folds, diamonds show means. Standard deviations describe fold variation and are not confidence intervals.")

    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    matrix = np.array([[final["tn"], final["fp"]], [final["fn"], final["tp"]]])
    sns.heatmap(matrix, annot=False, cmap=sns.light_palette(BENIGN, as_cmap=True), cbar=False,
                linewidths=4, linecolor=PAPER, ax=ax, square=True)
    descriptions = [["Benign, correctly classified", "Benign, flagged malignant"],
                    ["Malignant, missed", "Malignant, correctly flagged"]]
    for row in range(2):
        for col in range(2):
            value = matrix[row, col]
            color = "white" if value > matrix.max() * .6 else INK
            ax.text(col + .5, row + .43, str(value), ha="center", va="center", color=color, fontsize=30, weight="bold")
            ax.text(col + .5, row + .68, descriptions[row][col].replace(", ", "\n"), ha="center", va="center", color=color, fontsize=8, linespacing=1.5)
    ax.set(xticklabels=["Benign", "Malignant"], yticklabels=["Benign", "Malignant"], xlabel="Predicted class", ylabel="Observed diagnosis")
    ax.tick_params(length=0)
    plt.setp(ax.get_yticklabels(), rotation=0)
    save(fig, assets / "holdout-confusion.svg", "Final errors at the frozen threshold",
         f"On {final['n']} holdout samples: {final['tn']} true negatives, {final['fp']} false positives, {final['fn']} false negatives, and {final['tp']} true positives. Malignant is the positive class.")

    predictions = pd.read_csv(project / "reports/metrics/holdout_predictions.csv")
    observed, mean_probability = calibration_curve(predictions.target, predictions.probability_malignant, n_bins=5, strategy="quantile")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), gridspec_kw={"width_ratios": [1.2, 1]})
    axes[0].plot([0, 1], [0, 1], "--", color="#afbbb5", linewidth=1, label="Perfect calibration")
    axes[0].plot(mean_probability, observed, "o-", c=BENIGN, markersize=6, label="Five quantile bins")
    axes[0].set(xlabel="Mean estimated malignant probability", ylabel="Observed malignant fraction", xlim=(-.03, 1.03), ylim=(-.03, 1.03))
    axes[0].legend(frameon=False, fontsize=8)
    for label in [0, 1]:
        rows = predictions.loc[predictions.target == label]
        axes[1].hist(rows.probability_malignant, bins=np.linspace(0, 1, 16), color=BENIGN if label == 0 else MALIGNANT,
                     alpha=.6, label="Observed benign" if label == 0 else "Observed malignant", histtype="stepfilled")
    axes[1].axvline(final["threshold"], color=INK, linestyle="--", linewidth=1, label="Frozen threshold")
    axes[1].set(xlabel="Estimated malignant probability", ylabel="Samples")
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout(w_pad=2)
    save(fig, assets / "calibration.svg", "Ranking quality and probability quality are different questions",
         "Holdout reliability plot with five approximately equal-sized bins, beside probability histograms by observed class. Small bin counts make the reliability curve uncertain; no recalibration was fitted to these observations.")
