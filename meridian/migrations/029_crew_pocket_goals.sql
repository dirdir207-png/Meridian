-- 029: retain Crew's observed target on each pocket/subaccount.
-- A goal is a pocket target, not a commitment amount; NULL means Crew did not report one.
ALTER TABLE financial_accounts ADD COLUMN goal_target REAL;
