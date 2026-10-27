## Public portfolio publication · 2026-10-27

The approved study is being published from `robcalimente/breast-cancer-case-study` to https://robcalimente.github.io/breast-cancer-case-study/. GitHub Actions verifies the frozen analysis, executes all four notebooks, checks six rendered pages, and deploys main. The portfolio features the study second among five selected projects. The existing owner-private Sites preview remains available as a review copy.

Generated `dist/` hosting output is excluded from Quarto resources to prevent recursive copies on subsequent renders. Public hosting changes do not alter the frozen model, threshold, splits, or evaluation results.

# Project handoff

Built October 26, 2026. This is a completed first version for visual and editorial review.

The study is independent of the main portfolio repository. Its six-chapter Quarto home page is generated from `site/index.qmd.in`; `src/cancer_study/publish.py` fills it with saved results and writes the methods page. Four notebooks call and inspect the shared package. Do not create a second modeling implementation in the report.

The accepted source and protocol are frozen. Logistic regression was selected using the declared development rule. Final holdout: 39 TP, 72 TN, zero FP, three FN; n=114. Threshold 0.5478283925728269. The illustrative 95% development-sensitivity target was not attained on the holdout. There has been no model revision based on holdout errors.

The published result is protected by `reports/metrics/freeze.json` and `evaluation-lock.json`. Do not delete these locks to iterate on this holdout. Visual or prose edits do not require retraining. A revised modeling study needs fresh evaluation evidence.

Completed validation: 17 Python tests, six JavaScript checks against Python counts, fresh development refit with matching results, clean-kernel execution of all four notebooks, Quarto rendering, and local link/asset/anchor/alt-text checks. Desktop preview was inspected through a native browser. A dedicated mobile viewport inspection was not completed with the available browser controls; responsive CSS is present.

The `.openai/hosting.json` file identifies the owner-private Sites preview. Preserve that identity and audience on edits. The GitHub Actions workflow verifies the study and uploads static output; it does not publish GitHub Pages. No public GitHub repository has been created for this study yet.

Use `./study preview` on the prepared machine, or install the prerequisites in README for a fresh checkout. `.tools/` and `.venv/` are ignored local conveniences. The existing portfolio site is unchanged.

Readability revision: Rob approved the content and asked for a calmer theme and a clear reading order. The home page now uses one article column, white and charcoal with a blue link accent, a numbered reading outline, compact tables, and charts after their explanatory text. The first chart follows the dataset introduction. The dark model section and alternating text/figure columns were removed. Plot backgrounds are white. This revision renders successfully and passes local resource, anchor, and alt-text checks. The analysis and frozen result are unchanged. A fresh screenshot review of the revision was limited by slow native browser controls.

October 27 editorial revision for review: Rob felt the simplified page had lost its character and looked like documentation. Keep its single reading path while restoring the study's subject and visual identity. The opening now asks “What does a model miss?” and shows all 114 holdout outcomes as source-derived marks, with the three missed malignant samples identified. Prose stays at a consistent 700px measure on desktop, while figures use a wider canvas. Serif reading typography, numbered chapters, a vertical preparation sequence, and the 6.1% missed-sample finding provide a stronger hierarchy. The contents list is collapsed so it does not dominate the opening. No analysis or threshold was revised.

This revision was visually checked through the connected Chrome browser at 1280 × 900 and 390 × 844. The narrow viewport loads the alternate outcome-map composition and has no page overflow. All chapter introductions share the same left edge and text width on desktop. The slider was checked at zero and reset to the development choice. Both outcome maps were checked against the frozen CSV by sample ID. Keep Rob's local review server running at http://localhost:4681/; he explicitly asked for it to remain available.

Biology revision for review: add a beginner's path from benign/malignant definitions through FNA sampling, digitized nuclei, and case-level features. The first chapter explicitly distinguishes nuclear measurements from the dimensions of the breast lump. A labeled schematic explains size, boundary shape, and image texture; the drawings have no diagnosis. The full ten-feature glossary and original-cohort details are expandable. The exploration chapter connects morphology to the task and reports the saved development medians. The evaluation explains error types and distinguishes retrospective model errors from clinical-care outcomes. A final expandable section distinguishes diagnosis, grade, stage, and biomarkers. Medical context cites NCI, feature definitions cite UCI and scikit-learn, and historical extraction/cohort details cite Wolberg and colleagues (1995). No new training or threshold decisions are made.

Operational notes: the current review server is static HTTP on port 4681, serving `site/_site`; keep it running for Rob's review. The local checkout contains untracked duplicate files with “2” in their names; leave them untouched. To synchronize checkouts, fetch and fast-forward Git history and copy the rendered output separately. Do not copy an entire `.git` tree over existing immutable Git objects.

Biology revision checks: the six-page render and local links/anchors/alt text pass. Both schematic SVGs parse and include an explicit explanation that the drawings have no diagnosis. The rendered glossary contains ten features and its expansion was checked in Chrome. The published median statements match the saved development results (17.4 malignant, 12.2 benign on the source scale). Chrome was checked at 1280 × 900 and 390 × 844; the mobile diagram loads the stacked composition and the expanded glossary has no page overflow. Frozen evaluation counts remain 39 TP, 72 TN, zero FP, three FN.
