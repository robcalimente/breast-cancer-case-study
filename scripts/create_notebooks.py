"""Create the four executable chapter notebooks. Run intentionally, not on every pipeline run."""
from pathlib import Path
import nbformat as nbf

PROJECT = Path(__file__).resolve().parents[1]
setup = '''from cancer_study.common import root, read_json
from IPython.display import SVG, display
import pandas as pd

project = root()
metrics_dir = project / "reports/metrics"
def figure(name):
    display(SVG(filename=str(project / "site/assets" / name)))
'''

chapters = {
    "01_data_audit": ("01 · Establish trust in the data", [
        ("markdown", "The unit of observation is a breast-mass sample. Before modeling, I need to establish the source, the meaning of the label, and whether the table meets a documented contract. The pipeline is a prerequisite: run `uv run cancer-study run` from a clean checkout before these notebooks. Each notebook then executes independently from a fresh kernel."),
        ("code", setup),
        ("markdown", "## Preserve the source\n\nThe accepted UCI snapshot is retained with a source manifest. A changed checksum stops processing rather than silently accepting a different dataset."),
        ("code", 'from cancer_study.ingest import ingest\nfrom cancer_study.datasets import assign_splits, model_inputs\n\nframe, quality = ingest(project)\npartitioned = assign_splits(project, frame)\nsource = read_json(project / "data/source.json")\ndisplay(pd.Series(source, name="source manifest"))'),
        ("markdown", "## Validate before transforming\n\nNo values are imputed and no rows are removed. Zeros are allowed. Deliberately malformed test fixtures demonstrate rejection behavior; they are not presented as defects in the original data."),
        ("code", 'display(pd.Series({k: v for k, v in quality.items() if k != "checks"}, name="quality report"))\ndisplay(pd.DataFrame({"check": quality["checks"], "status": "passed"}))'),
        ("markdown", "## Persist the partition\n\nThe stratified 80/20 split is assigned once with seed 42 and saved by sample ID. Source validation covers the ingestion; exploration that informs choices uses development data. The source has no duplicate vectors, though the available metadata cannot establish patient independence beyond sample IDs."),
        ("code", 'display(partitioned.groupby(["partition", "diagnosis"]).size().unstack(fill_value=0))\nx, y = model_inputs(partitioned)\nassert x.shape[1] == 30\nassert not {"sample_id", "diagnosis", "target", "partition"} & set(x.columns)\nassert y.eq(1).equals(partitioned.diagnosis.eq("M"))\nprint("Identifier and label excluded. Malignant is positive.")'),
        ("markdown", "## Query the validated table\n\nDuckDB provides a readable SQL layer over the same validated rows. Cohort counts include both partitions for accounting; feature summaries used in exploration are restricted to development."),
        ("code", 'import duckdb\n\nwith duckdb.connect() as connection:\n    connection.register("samples", partitioned)\n    sql = (project / "sql/cohort_summary.sql").read_text()\n    print(sql)\n    display(connection.execute(sql).df())'),
        ("markdown", "## Decision\n\nThe accepted source passes the contract, so retain its observations and measurements as supplied. Exclude the identifier from predictors, keep malignant as the positive class, and preserve the saved split for all later work."),
    ]),
    "02_exploration": ("02 · Investigate the signal", [
        ("markdown", "The goal is to understand class overlap and related measurements using development data. These figures explain the modeling choices; none is a clinical decision rule."),
        ("code", setup + '\nfrom cancer_study.datasets import load_development\ndevelopment = load_development(project)\nassert development.partition.eq("development").all()\nprint(f"Exploring {len(development)} development samples.")'),
        ("markdown", "## First look: separation and overlap\n\nEach point is one sample. Mean radius and worst concave points show a visible relationship with the recorded class, while overlapping observations make a one-feature rule inadequate."),
        ("code", 'figure("sample-map.svg")'),
        ("markdown", "## Compare distributions\n\nDensity curves summarize the observed development distributions. Their smoothing is descriptive; the model uses the original numeric features. Vertical lines indicate class medians."),
        ("code", 'figure("distributions.svg")\nwith __import__("duckdb").connect() as connection:\n    connection.register("samples", development)\n    display(connection.execute((project / "sql/feature_summary.sql").read_text()).df())'),
        ("markdown", "## Check related measurements\n\nRadius, perimeter, and area describe related aspects of size. Correlation motivates comparing a regularized model with nonlinear alternatives; it does not establish causation or justify a full-data supervised feature ranking."),
        ("code", 'figure("correlations.svg")\ndisplay(pd.Series(read_json(metrics_dir / "exploration.json")))'),
        ("markdown", "## Decision\n\nRetain all thirty features and use regularization. Fit scaling inside validation folds for scale-sensitive models. Compare a small, fixed set of candidates under the same protocol. Measurement units are not asserted where the source dictionary does not establish them."),
    ]),
    "03_model_selection": ("03 · Choose a model and a threshold", [
        ("markdown", "The protocol precedes training. The notebooks inspect the shared pipeline and its saved artifacts; they do not provide a second implementation. The cached freeze is verified before any final evaluation is read."),
        ("code", setup + '\nfrom cancer_study.datasets import load_development\nfrom cancer_study.train import train, candidates\nprotocol = read_json(project / "protocol.json")\nfreeze = train(project, load_development(project))\ndisplay(pd.Series(protocol))'),
        ("markdown", "## Fit preprocessing within folds\n\nCandidates share five stratified development folds. SVM calibration wraps the entire scaler-model pipeline, so its internal validation rows do not fit the scaler. No oversampling or feature selection is used."),
        ("code", 'for name, estimator in candidates(protocol).items():\n    print(name)\n    display(estimator)'),
        ("markdown", "## Compare candidates fairly\n\nThe majority baseline supplies a reference. Mean validation ROC-AUC determines ranking; the simplest candidate within 0.005 of the highest candidate mean wins. The fold SD is descriptive, not a confidence interval. The selected candidate score is optimistic after selection."),
        ("code", 'cv = pd.read_csv(metrics_dir / "cross_validation.csv")\ndisplay(cv.groupby("model").roc_auc.agg(["mean", "std", "min", "max"]))\nfigure("model-comparison.svg")\nprint("Selected:", freeze["model"])'),
        ("markdown", "## Select an illustrative operating threshold\n\nThe predeclared rule maximizes specificity among development out-of-fold thresholds reaching at least 95% sensitivity. This illustrates a preference for fewer missed malignant samples, not an established clinical target. Development predictions are exploratory after selection."),
        ("code", 'development_result = read_json(metrics_dir / "development.json")\ndisplay(pd.Series(development_result))\nprint("Frozen threshold:", freeze["threshold"])\nprint("Frozen model SHA-256:", freeze["model_sha256"])'),
        ("markdown", "## Decision\n\nFit the chosen pipeline on all development samples and freeze its artifact and threshold. The final holdout will evaluate that fixed decision. Error inspection after the holdout does not trigger model revision."),
    ]),
    "04_final_evaluation": ("04 · Evaluate the frozen decision", [
        ("markdown", "Final evaluation answers a narrower question than model development: how did the frozen decision perform on the reserved samples? The final predictions were generated after the model freeze and are reused on compatible reruns."),
        ("code", setup + '\nfrom cancer_study.evaluate import metrics\nfinal = read_json(metrics_dir / "holdout.json")\npredictions = pd.read_csv(metrics_dir / "holdout_predictions.csv", dtype={"sample_id": str}, float_precision="round_trip")\ndisplay(pd.Series(final))'),
        ("markdown", "## Count both kinds of error\n\nMalignant is positive. Sensitivity measures the fraction of observed malignant samples detected; specificity measures the fraction of observed benign samples correctly cleared. Show the denominators as well as percentages."),
        ("code", 'figure("holdout-confusion.svg")\nprint(f"Malignant detected: {final[\'tp\']}/{final[\'tp\'] + final[\'fn\']}")\nprint(f"Benign cleared: {final[\'tn\']}/{final[\'tn\'] + final[\'fp\']}")\nrecomputed = metrics(predictions.target, predictions.probability_malignant, final["threshold"])\nfor key in ["tp", "tn", "fp", "fn"]:\n    assert recomputed[key] == final[key]'),
        ("markdown", "## Keep uncertainty visible\n\nThe sensitivity and specificity intervals use the Wilson score method at 95%. They condition on this model and this holdout sampling frame, and do not include all model-development uncertainty or external transportability."),
        ("code", 'for name in ["sensitivity", "specificity"]:\n    lo, hi = final[f"{name}_wilson_95"]\n    print(f"{name.capitalize()}: {final[name]:.1%} (95% Wilson: {lo:.1%}–{hi:.1%})")'),
        ("markdown", "## Inspect probability quality\n\nROC-AUC measures ranking. Brier score and the reliability plot describe probability quality. Five quantile bins are used, with limited observations per bin; the curve is uncertain and no recalibration is fitted here."),
        ("code", 'figure("calibration.svg")'),
        ("markdown", "## Inspect every mistake\n\nThe table below is complete, not a selected set of examples. Observed labels are benchmark labels, not independently adjudicated ground truth. These observations were examined after final evaluation; they are not used to change the pipeline."),
        ("code", 'errors = predictions.loc[~predictions.correct].copy()\ndisplay(errors)\nprint(f"{len(errors)} errors out of {len(predictions)} holdout samples.")'),
        ("markdown", "## Conclusion and next evidence\n\nThe measurements contain a strong signal for the recorded class in this dataset. The performance claim remains bounded by a small historical cohort and an internal random holdout. The supplied table does not enable demographic or institutional subgroup checks, establish longitudinal patient independence, or support population screening claims.\n\nIndependent, compatible data would be required to evaluate external validity. Revising the model after examining these errors would require fresh evaluation evidence."),
    ]),
}

for name, (title, content) in chapters.items():
    notebook = nbf.v4.new_notebook()
    notebook.metadata = {
        "kernelspec": {"display_name": "Python 3 (study)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    }
    notebook.cells = [nbf.v4.new_markdown_cell(f"---\ntitle: \"{title}\"\n---")]
    for kind, source in content:
        descriptions = {
            "sample-map.svg": "Development samples by mean radius and worst concave points, showing class separation and overlap.",
            "distributions.svg": "Development class distributions of mean radius, mean texture, and worst concave points, with medians and overlapping ranges.",
            "correlations.svg": "Pearson correlations among ten mean measurements, with strong relationships between size-related features.",
            "model-comparison.svg": "Five development validation-fold ROC-AUC results for a majority baseline, logistic regression, calibrated RBF SVM, and random forest.",
            "holdout-confusion.svg": "Final holdout: 72 true negatives, zero false positives, three false negatives, and 39 true positives.",
            "calibration.svg": "Holdout reliability plot using five quantile bins and probability histograms by observed diagnosis.",
        }
        for filename, description in descriptions.items():
            if kind == "code" and f'figure("{filename}")' in source:
                source = f'#| fig-alt: "{description}"\n' + source
        cell = nbf.v4.new_code_cell(source) if kind == "code" else nbf.v4.new_markdown_cell(source)
        notebook.cells.append(cell)
    nbf.write(notebook, PROJECT / f"notebooks/{name}.ipynb")
    print(f"Created {name}.ipynb")
