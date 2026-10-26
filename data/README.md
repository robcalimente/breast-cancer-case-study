# Data dictionary and source policy

One row represents a breast-mass sample in the UCI Wisconsin Diagnostic Breast Cancer dataset. The source is retained in `raw/wdbc.data`, with its original dictionary in `raw/wdbc.names` and an accepted checksum in `source.json`.

Citation: Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1993). Breast Cancer Wisconsin (Diagnostic). UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B. License: CC BY 4.0, as documented by UCI. This repository does not change the data's license.

| Field | Meaning | Modeling role |
| --- | --- | --- |
| `sample_id` | Source numeric identifier, preserved as a string | Trace observations; excluded from predictors |
| `diagnosis` | B = benign, M = malignant | Source target |
| `target` | 0 = benign, 1 = malignant | Derived numeric target |
| `partition` | development or holdout | Persisted evaluation partition; excluded from predictors |

Ten properties are supplied as mean, standard error (`_se`), and worst (`_worst`, mean of the three largest values), giving thirty features. Source order is ten means, ten standard errors, then ten worst values. The source does not establish physical units for these columns; the report labels their scale accordingly.

| Property | Source definition |
| --- | --- |
| radius | Mean distance from the nucleus center to perimeter points |
| texture | Standard deviation of grayscale values |
| perimeter | Nucleus perimeter |
| area | Nucleus area |
| smoothness | Local variation in radius lengths |
| compactness | Perimeter² / area − 1, as documented by the source |
| concavity | Severity of concave portions of the contour |
| concave_points | Number of concave portions of the contour |
| symmetry | Nucleus symmetry |
| fractal_dimension | Coastline approximation − 1, as documented by the source |

No values are imputed, resampled, rounded, or deleted in processing. Legitimate zero values remain. Source bytes, processed Parquet, persisted split IDs, quality reports, and the frozen result artifacts are versioned together for inspection. The environment, rendered site, and temporary caches are not versioned. Float formatting in exported prediction CSVs retains round-trip precision.

The source has unique sample IDs and no duplicate feature vectors under the current contract. Different IDs are not independently verified patient identities; this source does not enable a longitudinal or institutional grouping audit.
