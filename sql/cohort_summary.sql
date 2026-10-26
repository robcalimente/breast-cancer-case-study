SELECT partition,
       CASE WHEN target = 1 THEN 'Malignant' ELSE 'Benign' END AS diagnosis,
       count(*) AS samples,
       round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY partition), 2) AS percent_within_partition
FROM samples
GROUP BY partition, target
ORDER BY partition, target;
