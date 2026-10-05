SET search_path TO npdo;

-- Drop old 6 tables if they exist
DROP TABLE IF EXISTS npdo.stats_sa_qlfs_labour_market_status_estimates;
DROP TABLE IF EXISTS npdo.stats_sa_qlfs_industry_estimates;
DROP TABLE IF EXISTS npdo.stats_sa_qlfs_occupation_estimates;
DROP TABLE IF EXISTS npdo.stats_sa_qlfs_neet_estimates;
DROP TABLE IF EXISTS npdo.stats_sa_qlfs_underemployed_estimates;
DROP TABLE IF EXISTS npdo.stats_sa_qlfs_formal_informal_employment_estimates;

-- Create one combined fact table
CREATE TABLE IF NOT EXISTS npdo.stats_sa_qlfs_estimates (
    id              SERIAL      PRIMARY KEY,
    province        INTEGER     NOT NULL,
    district        INTEGER     NOT NULL,
    municipality    INTEGER     NOT NULL,
    year            INTEGER     NOT NULL,
    quarter         INTEGER     NOT NULL,
    indicator_type  INTEGER     NOT NULL,
    indicator_code  INTEGER     NOT NULL,
    measure_type_id INTEGER     NOT NULL,
    measure_code    INTEGER     NOT NULL,
    value           INTEGER     NOT NULL
);

COMMENT ON TABLE npdo.stats_sa_qlfs_estimates
    IS 'Combined QLFS estimates — all indicators in one table. indicator_type distinguishes between status, industry, occupation, neet, underemployment, formal_informal.';
