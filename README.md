# From Sample to Signal

[Read the study](https://robcalimente.github.io/breast-cancer-case-study/) · [Rob’s portfolio](https://robcalimente.github.io/#breast-cancer-study)

A visual study of breast-mass classification by Rob Calimente: how source data becomes a validated table, an investigated signal, and an evaluated model decision.

The main deliverable is a Quarto case study. Four Python notebooks expose the analysis, and a shared Python package owns the computations. An interactive threshold explorer uses development predictions; the final holdout result remains fixed.

![Development samples plotted by mean radius and worst concave points, showing separation and overlap between benign and malignant labels.](site/assets/sample-map.svg)

The declared comparison selected logistic regression. At the development-selected threshold of 0.547828, it correctly classified 111 of 114 holdout samples. All three errors were missed malignant samples; one received an estimated malignant probability of only 6.1%.

| Final holdout measure | Result |
| --- | --- |
| Sensitivity | 39/42 = 92.9%; 95% Wilson interval 81.0–97.5% |
| Specificity | 72/72 = 100.0%; 95% Wilson interval 94.9–100.0% |
| Accuracy | 111/114 = 97.4% |
| ROC-AUC | 0.996 |

The 95% development-sensitivity target did not carry over to the holdout. The report keeps that gap, every error, and the uncertainty visible. These are results on one historical benchmark, not evidence of clinical readiness.

## Read the study

The six chapters cover the observation unit, source validation and lineage, exploratory analysis, model comparison, threshold tradeoffs, and final errors and uncertainty. See `index.qmd` for the generated narrative and `methods.qmd` for the full protocol.

| Skill | Inspectable evidence |
| --- | --- |
| Data engineering | Accepted source hash, strict schema checks, Parquet tables, persisted split IDs, SQL summaries, artifact manifest |
| Data analysis | Development-only distributions, related measurements, class overlap, SQL queries, interpretation and limitations |
| Data science | Fold-local preprocessing, fixed candidate comparison, development-selected threshold, frozen holdout evaluation, Wilson intervals |
| Communication | Six-chapter visual story, downloadable notebooks, annotated figures, keyboard-operable threshold exploration |

## Run locally

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), [Quarto 1.10.19](https://quarto.org/docs/download/), and Node.js 22+ for the browser-model checks. Python dependencies are pinned in `uv.lock`.

```bash
uv sync --frozen
uv run cancer-study run
uv run python scripts/execute_notebooks.py
uv run quarto preview --no-browser
```

Build a static site with `uv run quarto render`. Output is `site/_site/`. The site uses no external font, chart CDN, prediction API, or analytics service. The small threshold explorer is native JavaScript sharing a tested counting function with Node tests.

On the prepared local copy, `./study preview` starts the website using the included local tooling. `./study run`, `./study check`, `./study notebooks`, `./study reproduce`, and `./study render` provide the same steps without relying on globally installed commands. The ignored `.tools/` folder is a local convenience; a fresh clone uses the prerequisites above and `./study setup`.

## Verify the study

```bash
uv run pytest
node --test tests/explorer.test.mjs
uv run python scripts/reproduce_development.py
uv run python scripts/execute_notebooks.py
uv run quarto render
uv run python scripts/check_site.py
```

The main pipeline validates the source and split, verifies the model freeze, and reuses compatible final results. A changed training input or frozen artifact causes a failure. `reproduce_development.py` performs a fresh fit in a temporary workspace and checks the development results against the published artifacts without loading or evaluating the holdout.

Every notebook executes in a fresh kernel after the pipeline. Notebook outputs are retained for GitHub reading. Rendered chapters are linked from the case study; downloadable notebook copies live under `site/assets/notebooks/` after notebook execution.

The CI workflow repeats those checks and uploads the static site as a build artifact. It does not publish to GitHub Pages automatically.

The private Sites preview uses `uv run python scripts/stage_site.py` to copy verified Quarto output into its supported `dist/` directory. The analysis sources and Quarto output location remain the same.

## Files

```text
protocol.json                 Declared candidates, split, selection, threshold, and scope
data/raw/                     Original UCI snapshot and source documentation
data/source.json              Citation, URL, retrieval time, accepted checksum
data/processed/               Parquet tables and saved partition assignments
src/cancer_study/             Shared acquisition, validation, modeling, evaluation, figures
sql/                          Cohort accounting and development summaries
notebooks/                    Four executable chapters
reports/metrics/              Fold results, predictions, freeze, and final evaluation lock
reports/manifests/run.json     Environment and artifact hashes
site/                         Narrative template, visual system, and threshold explorer
index.qmd, methods.qmd         Generated report sources
scripts/                      Notebook execution and independent development reproduction
tests/                        Data contracts, evaluation accounting, and browser/Python agreement
```

Edit the home narrative in `site/index.qmd.in`, then rerun the pipeline. The methods page is generated by `src/cancer_study/publish.py`. Notebook generation is an intentional authoring step (`scripts/create_notebooks.py`); routine runs preserve the authored notebooks.

The original dataset, processed tables, and small result artifacts are committed together for inspection. Package environments, caches, and the rendered website are ignored. Runtime manifests record both code revision and file hashes; a dirty-tree flag distinguishes a development run from a committed revision.

## Evaluation boundary

Malignant is always the positive class. The 80/20 split is stratified with seed 42. The development experiment compares a majority baseline, regularized logistic regression, calibrated RBF SVM, and a random forest with fixed settings across five folds. The simplest candidate within 0.005 of the best mean ROC-AUC is selected. A development sensitivity target of 95% illustrates one decision preference and is not a clinical standard.

The final model and threshold are frozen before holdout evaluation. Published errors may be inspected, but they are not used to revise the model. A revised experiment needs fresh evaluation evidence; deleting locks does not create a fresh holdout. This historical benchmark does not establish clinical readiness, future-risk prediction, external validity, or subgroup fairness.

## Source and inspiration

Data: Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1993). [Breast Cancer Wisconsin (Diagnostic)](https://doi.org/10.24432/C5DW2B), UCI Machine Learning Repository. **CC BY 4.0**. See [data/README.md](data/README.md) and the original source dictionary. The data retains its original license.

Subject inspiration: [Fitzpatrickmn/Machine-Learning-Cancer-Classifier](https://github.com/Fitzpatrickmn/Machine-Learning-Cancer-Classifier). This study uses an independent implementation and the original UCI source. The reference's histopathology cohort is a separate task and is not joined to this dataset or treated as a controlled modality comparison.

Project code and original prose: MIT; see [LICENSE](LICENSE). Third-party data and generated package assets retain their respective licenses.

## Public hosting

GitHub Actions verifies the frozen analysis, executes the four notebooks, renders the six-page Quarto site, and checks local links before deploying `main` to GitHub Pages. Pull requests run the same verification without deployment.

The fresh-refit check requires the same selected candidate and threshold, matching fold AUCs and development classifications, and probability agreement at `rtol=1e-8, atol=1e-9`. The unselected random forest has an explicit absolute tolerance of `0.005`: the Linux CI refit differed from the original Mac run by at most `0.003612`, with unchanged fold AUCs and classifications. This tolerance applies only to fresh development refits. The published model, predictions, and evaluation remain frozen and checked by their SHA-256 hashes.
