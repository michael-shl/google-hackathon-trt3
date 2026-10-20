-- Neighborhood need per business (owner: P2). Feeds get_neighborhood and equity_audit.
--
-- Why this is not a simple join to tract_demographics:
--   * tract_demographics (from load.sh) covers the 7 tracts around the employer blocks; only 2 of the
--     corridor's 230 businesses fall inside them.
--   * The public tract SHAPES in BigQuery are 2010 vintage, but the newest ACS (2016-2020 5-year,
--     censustract_2020_5yr) uses 2020 tract IDs. San Francisco split several tracts in 2020
--     (e.g. 0176.01 -> 0176.02/.03/.04).
-- Method (Census convention: a split keeps the 4-digit base number):
--   1. point-in-polygon each business into its 2010 tract;
--   2. 'exact'       : that tract ID still exists in ACS 2020 -> use it;
--      'split_base'  : otherwise combine the NEW 2020 tracts with the same base (IDs absent in 2010),
--                      summing ACS counts before dividing (ratio of sums, not mean of rates).
-- Limitation (say it in the deck): for split tracts the need signal is the average over the 2010
-- tract's area, not the exact 2020 sub-tract.

CREATE OR REPLACE TABLE a4i_econ.business_tract AS
SELECT b.business_id, t.geo_id AS tract_2010
FROM a4i_econ.businesses AS b
JOIN `bigquery-public-data.geo_census_tracts.census_tracts_california` AS t
  ON ST_CONTAINS(t.tract_geom, ST_GEOGPOINT(b.longitude, b.latitude))
WHERE STARTS_WITH(t.geo_id, '06075');

CREATE OR REPLACE TABLE a4i_econ.business_need AS
WITH acs AS (
  SELECT LPAD(geo_id, 11, '0') AS geo_id,
         SAFE_CAST(total_pop AS FLOAT64) AS total_pop,
         SAFE_CAST(median_income AS FLOAT64) AS median_income,
         SAFE_CAST(poverty AS FLOAT64) AS poverty,
         SAFE_CAST(pop_determined_poverty_status AS FLOAT64) AS poverty_universe,
         SAFE_CAST(no_cars AS FLOAT64) AS no_cars,
         SAFE_CAST(households AS FLOAT64) AS households,
         SAFE_CAST(households_public_asst_or_food_stamps AS FLOAT64) AS assistance
  FROM `bigquery-public-data.census_bureau_acs.censustract_2020_5yr`
  WHERE STARTS_WITH(LPAD(geo_id, 11, '0'), '06075')
),
tracts_2010 AS (
  SELECT geo_id FROM `bigquery-public-data.geo_census_tracts.census_tracts_california`
  WHERE STARTS_WITH(geo_id, '06075')
),
business_tracts AS (
  SELECT DISTINCT tract_2010, tract_2010 IN (SELECT geo_id FROM acs) AS in_acs
  FROM a4i_econ.business_tract
),
new_2020 AS (
  -- 2020 tracts that did not exist in 2010, i.e. the products of a split
  SELECT geo_id FROM acs WHERE geo_id NOT IN (SELECT geo_id FROM tracts_2010)
),
crosswalk AS (
  -- 2010 tract -> the 2020 ACS tract(s) that cover it
  SELECT tract_2010, tract_2010 AS tract_2020, 'exact' AS method
  FROM business_tracts WHERE in_acs
  UNION ALL
  SELECT b.tract_2010, n.geo_id, 'split_base'
  FROM business_tracts AS b
  JOIN new_2020 AS n ON SUBSTR(n.geo_id, 1, 9) = SUBSTR(b.tract_2010, 1, 9)
  WHERE NOT b.in_acs
),
need_2010 AS (
  SELECT c.tract_2010,
         ANY_VALUE(c.method) AS match_method,
         STRING_AGG(c.tract_2020, ',' ORDER BY c.tract_2020) AS acs_tracts,
         SUM(a.total_pop) AS total_pop,
         SAFE_DIVIDE(SUM(a.median_income * a.total_pop), SUM(IF(a.median_income IS NULL, 0, a.total_pop))) AS median_income,
         SAFE_DIVIDE(SUM(a.poverty), SUM(a.poverty_universe)) AS poverty_rate,
         SAFE_DIVIDE(SUM(a.no_cars), SUM(a.households)) AS no_vehicle_rate,
         SAFE_DIVIDE(SUM(a.assistance), SUM(a.households)) AS assistance_rate
  FROM crosswalk AS c JOIN acs AS a ON a.geo_id = c.tract_2020
  GROUP BY c.tract_2010
)
SELECT bt.business_id, bt.tract_2010 AS tract, n.acs_tracts, n.match_method,
       n.total_pop, n.median_income, n.poverty_rate, n.no_vehicle_rate, n.assistance_rate
FROM a4i_econ.business_tract AS bt
LEFT JOIN need_2010 AS n USING (tract_2010);
