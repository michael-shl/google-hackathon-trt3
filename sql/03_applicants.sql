-- Simulated application queue for the Main Street relief track (owners: P3 + P6; edit freely).
-- The BUSINESSES are real Central Market registrations; the APPLICATIONS (amounts, needs) are
-- SIMULATED. Say so in the deck.
--
-- Deliberate mix, chosen from graph reach (GRAPH_TABLE ... -[:Supplies]->{1,2} ..., 2026-10-20):
--   hubs (very large 2-hop reach)      : Sour Flour (145), Cumaica Coffee (145)
--   mid-band (5-25 exposed at 2 hops)  : Steel + Lacquer (24), A & A Legal (22), G.Rabbit (20),
--                                        Extraveganza Eatery (18), Chico's Pizza (15)
--   leaves (no outgoing supply edges)  : Eddy St Bodega, Bluebird Office Supplies,
--                                        Mo'z Cafe (NAICS recorded as '72' only, so the edge
--                                        generator cannot see it: a data-visibility bias example;
--                                        also has a REAL SBA 7(a) loan)
--   SBA borrower                       : The Bite (two REAL SBA 7(a) loans)
-- Total requested $134,500 against a $50,000 fund (over-subscribed on purpose).
CREATE OR REPLACE TABLE a4i_econ.applicants AS
SELECT * FROM UNNEST([
  STRUCT('16'  AS business_id, 25000 AS requested_amount, 'Oven replacement after a breakdown' AS stated_need),
  STRUCT('24',  20000, 'Roaster repair; wholesale orders down'),
  STRUCT('39',  15000, 'Utility arrears after a slow quarter'),
  STRUCT('182', 10000, 'Office lease renewal'),
  STRUCT('201', 12000, 'Lost weekday lunch trade'),
  STRUCT('109', 10000, 'Rent increase'),
  STRUCT('186',  8000, 'Delivery vehicle repair'),
  STRUCT('73',   5000, 'Refrigeration failure'),
  STRUCT('60',   7500, 'Inventory financing'),
  STRUCT('170', 10000, 'Payroll gap after a slow quarter'),
  STRUCT('65',  12000, 'Equipment loan repayment pressure')
]);
