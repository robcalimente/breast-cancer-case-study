-- Development data only: this query supports exploratory interpretation.
SELECT diagnosis, count(*) AS samples,
       median(radius_mean) AS median_radius_mean,
       median(texture_mean) AS median_texture_mean,
       median(concave_points_worst) AS median_concave_points_worst,
       quantile_cont(radius_mean, 0.25) AS radius_q25,
       quantile_cont(radius_mean, 0.75) AS radius_q75
FROM samples
WHERE partition = 'development'
GROUP BY diagnosis
ORDER BY diagnosis;
