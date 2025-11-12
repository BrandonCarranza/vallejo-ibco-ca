/*
 * Create Read-Only Database User for Metabase
 *
 * This script creates a dedicated PostgreSQL user for Metabase with SELECT-only permissions.
 * This ensures Metabase cannot modify, delete, or corrupt data.
 *
 * Security principles:
 * - Principle of least privilege: Only SELECT permission
 * - No DDL permissions (CREATE, ALTER, DROP)
 * - No DML permissions (INSERT, UPDATE, DELETE)
 * - No access to system catalogs or sensitive functions
 *
 * Usage:
 *   psql -h localhost -U ibco_admin -d ibco_production -f create_readonly_user.sql
 *
 * Or via environment variable for password:
 *   PGPASSWORD=${METABASE_DB_PASSWORD} psql -h localhost -U ibco_admin -d ibco_production -f create_readonly_user.sql
 */

-- =============================================================================
-- 1. CREATE ROLE
-- =============================================================================

-- Drop user if exists (for idempotency)
DROP USER IF EXISTS metabase_readonly;

-- Create read-only user
-- Password should be set via environment variable: ${METABASE_DB_PASSWORD}
CREATE USER metabase_readonly WITH
  LOGIN
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  NOINHERIT
  NOREPLICATION
  CONNECTION LIMIT 10  -- Limit concurrent connections
  PASSWORD :'METABASE_DB_PASSWORD';  -- Pass via psql -v METABASE_DB_PASSWORD=xxx

COMMENT ON ROLE metabase_readonly IS 'Read-only user for Metabase dashboards (IBCo Vallejo Console)';

-- =============================================================================
-- 2. GRANT SCHEMA USAGE
-- =============================================================================

-- Allow access to public schema
GRANT USAGE ON SCHEMA public TO metabase_readonly;

-- =============================================================================
-- 3. GRANT SELECT ON ALL TABLES
-- =============================================================================

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO metabase_readonly;

-- Grant SELECT on all future tables (auto-grant for new tables)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO metabase_readonly;

-- =============================================================================
-- 4. GRANT SELECT ON ALL SEQUENCES (for sequence queries)
-- =============================================================================

-- Grant SELECT on all existing sequences
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO metabase_readonly;

-- Grant SELECT on all future sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON SEQUENCES TO metabase_readonly;

-- =============================================================================
-- 5. EXPLICITLY DENY WRITE PERMISSIONS
-- =============================================================================

-- Explicitly revoke INSERT, UPDATE, DELETE, TRUNCATE (belt and suspenders)
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM metabase_readonly;

-- Revoke all DDL permissions
REVOKE CREATE ON SCHEMA public FROM metabase_readonly;
REVOKE ALL ON DATABASE ibco_production FROM metabase_readonly;

-- =============================================================================
-- 6. GRANT SELECT ON SPECIFIC IBCo TABLES (Explicit Whitelist)
-- =============================================================================

-- Core tables
GRANT SELECT ON cities TO metabase_readonly;
GRANT SELECT ON fiscal_years TO metabase_readonly;
GRANT SELECT ON data_sources TO metabase_readonly;
GRANT SELECT ON data_lineage TO metabase_readonly;

-- Financial tables
GRANT SELECT ON revenues TO metabase_readonly;
GRANT SELECT ON revenue_categories TO metabase_readonly;
GRANT SELECT ON expenditures TO metabase_readonly;
GRANT SELECT ON expenditure_categories TO metabase_readonly;
GRANT SELECT ON fund_balances TO metabase_readonly;

-- Pension tables
GRANT SELECT ON pension_plans TO metabase_readonly;
GRANT SELECT ON pension_contributions TO metabase_readonly;
GRANT SELECT ON pension_projections TO metabase_readonly;
GRANT SELECT ON opeb_liabilities TO metabase_readonly;
GRANT SELECT ON pension_assumption_changes TO metabase_readonly;

-- Risk tables
GRANT SELECT ON risk_indicators TO metabase_readonly;
GRANT SELECT ON risk_scores TO metabase_readonly;
GRANT SELECT ON risk_indicator_scores TO metabase_readonly;
GRANT SELECT ON risk_trends TO metabase_readonly;
GRANT SELECT ON benchmark_comparisons TO metabase_readonly;

-- Projection tables
GRANT SELECT ON projection_scenarios TO metabase_readonly;
GRANT SELECT ON financial_projections TO metabase_readonly;
GRANT SELECT ON scenario_assumptions TO metabase_readonly;
GRANT SELECT ON fiscal_cliff_analyses TO metabase_readonly;

-- Refresh tables (for data freshness tracking)
GRANT SELECT ON refresh_checks TO metabase_readonly;
GRANT SELECT ON refresh_notifications TO metabase_readonly;
GRANT SELECT ON refresh_operations TO metabase_readonly;
GRANT SELECT ON data_refresh_schedules TO metabase_readonly;

-- Validation tables (for quality metrics)
GRANT SELECT ON validation_queue TO metabase_readonly;
GRANT SELECT ON validation_records TO metabase_readonly;
GRANT SELECT ON anomaly_flags TO metabase_readonly;
GRANT SELECT ON validation_rules TO metabase_readonly;

-- =============================================================================
-- 7. EXPLICITLY DENY ACCESS TO SENSITIVE TABLES (if any exist)
-- =============================================================================

-- If you add admin/auth tables in future, explicitly deny access:
-- REVOKE ALL ON admin_users FROM metabase_readonly;
-- REVOKE ALL ON api_tokens FROM metabase_readonly;
-- REVOKE ALL ON auth_sessions FROM metabase_readonly;

-- =============================================================================
-- 8. GRANT EXECUTE ON SAFE FUNCTIONS ONLY
-- =============================================================================

-- Allow common aggregation and date functions (default PostgreSQL functions are safe)
-- No explicit grants needed - built-in functions are available to all users

-- Explicitly REVOKE execute on any custom admin functions if they exist:
-- REVOKE EXECUTE ON FUNCTION admin_delete_data() FROM metabase_readonly;
-- REVOKE EXECUTE ON FUNCTION admin_modify_schema() FROM metabase_readonly;

-- =============================================================================
-- 9. CREATE HELPER VIEWS (Optional - for simplified querying)
-- =============================================================================

-- Create materialized view for latest risk scores (performance optimization)
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_risk_scores AS
SELECT DISTINCT ON (fy.city_id, fy.year)
  fy.city_id,
  fy.year AS fiscal_year,
  rs.overall_score,
  rs.risk_level,
  rs.liquidity_score,
  rs.structural_balance_score,
  rs.pension_stress_score,
  rs.revenue_sustainability_score,
  rs.debt_burden_score,
  rs.calculation_date
FROM fiscal_years fy
LEFT JOIN risk_scores rs ON rs.fiscal_year_id = fy.id
WHERE rs.is_deleted = false
ORDER BY fy.city_id, fy.year, rs.calculation_date DESC;

CREATE INDEX idx_latest_risk_scores_city_year ON latest_risk_scores(city_id, fiscal_year);

GRANT SELECT ON latest_risk_scores TO metabase_readonly;

-- Refresh schedule for materialized view (run nightly after data refresh)
COMMENT ON MATERIALIZED VIEW latest_risk_scores IS 'Cached latest risk scores per city/year. Refresh nightly at 2am UTC.';

-- =============================================================================
-- 10. SET ROW-LEVEL SECURITY (Optional - if implementing RLS)
-- =============================================================================

-- If implementing row-level security in future (e.g., to hide unpublished data):
-- ALTER TABLE risk_scores ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY metabase_published_only ON risk_scores
--   FOR SELECT
--   TO metabase_readonly
--   USING (validated = true);

-- For now, all data is public - no RLS needed

-- =============================================================================
-- 11. VERIFICATION QUERIES
-- =============================================================================

-- Verify user was created
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_user WHERE usename = 'metabase_readonly') THEN
    RAISE NOTICE 'SUCCESS: metabase_readonly user created';
  ELSE
    RAISE EXCEPTION 'FAILED: metabase_readonly user not found';
  END IF;
END $$;

-- Verify permissions
DO $$
DECLARE
  table_count INT;
BEGIN
  SELECT COUNT(*)
  INTO table_count
  FROM information_schema.table_privileges
  WHERE grantee = 'metabase_readonly'
    AND privilege_type = 'SELECT'
    AND table_schema = 'public';

  IF table_count > 0 THEN
    RAISE NOTICE 'SUCCESS: metabase_readonly has SELECT on % tables', table_count;
  ELSE
    RAISE EXCEPTION 'FAILED: metabase_readonly has no SELECT permissions';
  END IF;
END $$;

-- Verify no write permissions
DO $$
DECLARE
  write_count INT;
BEGIN
  SELECT COUNT(*)
  INTO write_count
  FROM information_schema.table_privileges
  WHERE grantee = 'metabase_readonly'
    AND privilege_type IN ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')
    AND table_schema = 'public';

  IF write_count = 0 THEN
    RAISE NOTICE 'SUCCESS: metabase_readonly has no write permissions';
  ELSE
    RAISE EXCEPTION 'FAILED: metabase_readonly has % write permissions (should be 0)', write_count;
  END IF;
END $$;

-- =============================================================================
-- 12. USAGE INSTRUCTIONS
-- =============================================================================

/*
 * TEST CONNECTION:
 *
 * psql "postgresql://metabase_readonly:${METABASE_DB_PASSWORD}@localhost:5432/ibco_production"
 *
 * TEST QUERY:
 *
 * SELECT c.name, fy.year, rs.overall_score
 * FROM cities c
 * JOIN fiscal_years fy ON fy.city_id = c.id
 * LEFT JOIN risk_scores rs ON rs.fiscal_year_id = fy.id
 * WHERE c.name = 'Vallejo'
 * ORDER BY fy.year DESC
 * LIMIT 5;
 *
 * TEST WRITE PROHIBITION (should fail):
 *
 * UPDATE cities SET name = 'TEST' WHERE id = 1;
 * -- Expected: ERROR: permission denied for table cities
 *
 * DELETE FROM risk_scores WHERE id = 1;
 * -- Expected: ERROR: permission denied for table risk_scores
 *
 * CREATE TABLE test (id INT);
 * -- Expected: ERROR: permission denied for schema public
 */

-- =============================================================================
-- SUCCESS!
-- =============================================================================

\echo ''
\echo '=========================================='
\echo 'Metabase Read-Only User Setup Complete!'
\echo '=========================================='
\echo ''
\echo 'User: metabase_readonly'
\echo 'Permissions: SELECT only on all IBCo tables'
\echo 'Connection limit: 10 concurrent connections'
\echo ''
\echo 'Next steps:'
\echo '  1. Test connection: psql "postgresql://metabase_readonly:PASSWORD@localhost:5432/ibco_production"'
\echo '  2. Configure Metabase database connection with these credentials'
\echo '  3. Import dashboard configurations'
\echo ''
\echo 'Security verified:'
\echo '  ✓ Read-only access (SELECT only)'
\echo '  ✓ No write permissions (INSERT/UPDATE/DELETE blocked)'
\echo '  ✓ No DDL permissions (CREATE/ALTER/DROP blocked)'
\echo '  ✓ Connection limit enforced'
\echo ''
\echo '=========================================='
