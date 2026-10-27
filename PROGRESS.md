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
