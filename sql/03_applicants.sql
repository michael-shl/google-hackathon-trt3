-- Simulated application queue for the Main Street relief track (owners: P3 + P6; edit freely).
-- The BUSINESSES are real Central Market registrations; the APPLICATIONS (amounts, needs) are
-- SIMULATED. Say so in the deck.
--
-- Matched BY NAME, not business_id: the notebook load uses City registry IDs (e.g. 1051477-01-161)
-- while scripts/load.sh uses short numeric IDs, so IDs change when the data is reloaded. The ASSERT
-- at the end fails loudly if a name stops matching.
--
-- Deliberate mix, chosen from graph reach (-[:Supplies]->{1,2}, notebook load of 2026-10-20 17:15 UTC):
--   hubs (very large 2-hop reach)      : Sour Flour (148), Cumaica Coffee (148)
--   mid-band (5-25 exposed at 2 hops)  : Steel + Lacquer (23), A & A Legal (22), G.Rabbit (18),
--                                        Monarch Beverage Catering (16), Chico's Pizza (16)
--   leaves (no outgoing supply edges)  : Eddy St Bodega, Bluebird Office Supplies,
--                                        Mo'z Cafe (NAICS recorded as '72' only, so the edge
--                                        generator cannot see it: a data-visibility bias example;
--                                        also has a REAL SBA 7(a) loan)
--   SBA borrower                       : The Bite (two REAL SBA 7(a) loans)
-- Total requested $134,500 against a $50,000 fund (over-subscribed on purpose).
CREATE OR REPLACE TABLE a4i_econ.applicants AS
WITH queue AS (
  SELECT * FROM UNNEST([
    STRUCT("Sour Flour" AS name, 25000 AS requested_amount, "Oven replacement after a breakdown" AS stated_need),
    STRUCT("Cumaica Coffee", 20000, "Roaster repair; wholesale orders down"),
    STRUCT("Steel + Lacquer", 15000, "Utility arrears after a slow quarter"),
    STRUCT("A & A Legal Service, Inc.", 10000, "Office lease renewal"),
    STRUCT("G.Rabbit", 12000, "Lost weekday lunch trade"),
    STRUCT("Monarch Beverage Catering LLC", 10000, "Event bookings cancelled"),
    STRUCT("Chico's Pizza", 8000, "Delivery vehicle repair"),
    STRUCT("Eddy St Bodega Inc", 5000, "Refrigeration failure"),
    STRUCT("Bluebird Office Supplies", 7500, "Inventory financing"),
    STRUCT("Mo'z Cafe Inc", 10000, "Payroll gap after a slow quarter"),
    STRUCT("The Bite", 12000, "Equipment loan repayment pressure")
  ])
)
SELECT MIN(b.business_id) AS business_id, q.requested_amount, q.stated_need
FROM queue AS q
JOIN a4i_econ.businesses AS b ON b.name = q.name
GROUP BY q.name, q.requested_amount, q.stated_need;

ASSERT (SELECT COUNT(*) FROM a4i_econ.applicants) = 11
  AS 'applicants: some names were not found in a4i_econ.businesses after a reload; edit sql/03_applicants.sql';
