-- Verify the Grant Desk "Data: BigQuery ... · real" label (owner: P1). Run in the BigQuery console.
-- Each query is independent; run them one at a time (select the query, then Run).

-- 1. The agent and the MCP Toolbox really queried BigQuery (mock mode never does).
--    Expect rows for grant-advisor (incl. a GRAPH query) and toolbox-identity after you click in the desk.
SELECT
  creation_time,
  SPLIT(user_email, '@')[OFFSET(0)] AS service_account,
  REGEXP_CONTAINS(query, r'^\s*GRAPH ') AS is_graph_query,
  REGEXP_CONTAINS(query, r'AS data_source') AS returns_data_source_column,
  SUBSTR(REGEXP_REPLACE(query, r'\s+', ' '), 1, 140) AS query_start
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 MINUTE)
  AND (user_email LIKE 'grant-advisor@%' OR user_email LIKE 'toolbox-identity@%')
ORDER BY creation_time DESC
LIMIT 20;

-- 2. The same row the MCP Toolbox returned (get_neighborhood), including its data_source label.
--    Expect: Eddy St Bodega Inc, poverty_rate 0.278, no_vehicle_rate 0.834, median_income 17052.
SELECT b.name, n.tract, n.match_method, n.total_pop, ROUND(n.median_income) AS median_income,
       ROUND(n.poverty_rate, 3) AS poverty_rate, ROUND(n.no_vehicle_rate, 3) AS no_vehicle_rate,
       'BigQuery a4i_econ · real (MCP Toolbox)' AS data_source
FROM a4i_econ.business_need AS n
JOIN a4i_econ.businesses AS b USING (business_id)
WHERE b.name = 'Eddy St Bodega Inc';

-- 3. The ranking's reach numbers come from the property graph (multi-hop GQL).
--    Expect: Cumaica Coffee and Sour Flour = 148 exposed within 2 hops (the desk's queue shows the same).
GRAPH a4i_econ.LocalEconomy
MATCH (seed:Business)-[:Supplies]->{1,2}(exposed:Business)
WHERE seed.name IN ('Cumaica Coffee', 'Sour Flour', 'G.Rabbit') AND exposed.business_id != seed.business_id
RETURN seed.name AS applicant, COUNT(DISTINCT exposed.business_id) AS exposed_2hop
ORDER BY exposed_2hop DESC;

-- 4. Mock businesses do NOT exist in BigQuery. If the desk ever shows these names, it is MOCK data.
--    Expect: mock_names_found = 0, real_applicants_found = 11.
SELECT
  COUNTIF(name IN ('Bayside Roasters', 'Golden Produce Wholesale', 'Kearny Kitchen', 'Larkin Event Hall')) AS mock_names_found,
  (SELECT COUNT(*) FROM a4i_econ.applicants JOIN a4i_econ.businesses USING (business_id)) AS real_applicants_found
FROM a4i_econ.businesses;
