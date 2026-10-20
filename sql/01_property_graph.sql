-- Property graph over the corridor (owner: P2). Run after scripts/load.sh; re-run after every load.
-- Traps (notebook §13): unbackticked `a4i_econ.x` in NODE/EDGE TABLES, bare table name in REFERENCES;
-- property names are global across the graph and their types must agree (`metres` is FLOAT64 in both).
-- Decision D6/D7: Supplies and DrawsFootfall are separate labels (different meaning and severity);
-- borrowed_from stays a lookup table (4 rows, banks are not corridor nodes).
CREATE OR REPLACE PROPERTY GRAPH a4i_econ.LocalEconomy
  NODE TABLES (
    a4i_econ.businesses
      KEY (business_id)
      LABEL Business PROPERTIES (business_id, name, naics4, zip, address, latitude, longitude),
    a4i_econ.employer_blocks
      KEY (block_id)
      LABEL Employer PROPERTIES (block_id, tract, jobs)
  )
  EDGE TABLES (
    a4i_econ.supplies
      KEY (edge_id)
      SOURCE KEY (supplier_id) REFERENCES businesses (business_id)
      DESTINATION KEY (buyer_id) REFERENCES businesses (business_id)
      LABEL Supplies PROPERTIES (intensity, metres),
    a4i_econ.draws_footfall_from
      KEY (edge_id)
      SOURCE KEY (block_id) REFERENCES employer_blocks (block_id)
      DESTINATION KEY (business_id) REFERENCES businesses (business_id)
      LABEL DrawsFootfall PROPERTIES (worker_share, metres)
  );
