-- Row Level Security (RLS) Policies for Zoning Worker
-- This file sets up security policies to control data access

-- Enable RLS on all tables
ALTER TABLE zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE standards ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_jobs ENABLE ROW LEVEL SECURITY;

-- Create user roles
DO $$
BEGIN
    -- Create roles if they don't exist
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'zone_reader') THEN
        CREATE ROLE zone_reader;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'zone_admin') THEN
        CREATE ROLE zone_admin;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'zone_worker') THEN
        CREATE ROLE zone_worker;
    END IF;
END
$$;

-- Grant basic permissions
GRANT USAGE ON SCHEMA public TO zone_reader, zone_admin, zone_worker;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO zone_admin, zone_worker;

-- =============================================================================
-- ZONES TABLE POLICIES
-- =============================================================================

-- Public read access to published zones
CREATE POLICY "Public zones read access" ON zones
    FOR SELECT
    USING (published = true AND is_current = true);

-- Admin full access to zones
CREATE POLICY "Admin zones full access" ON zones
    FOR ALL
    TO zone_admin
    USING (true)
    WITH CHECK (true);

-- Worker can insert and update zones
CREATE POLICY "Worker zones write access" ON zones
    FOR INSERT
    TO zone_worker
    WITH CHECK (true);

CREATE POLICY "Worker zones update access" ON zones
    FOR UPDATE
    TO zone_worker
    USING (true)
    WITH CHECK (true);

-- Worker can read all zones
CREATE POLICY "Worker zones read access" ON zones
    FOR SELECT
    TO zone_worker
    USING (true);

-- =============================================================================
-- STANDARDS TABLE POLICIES
-- =============================================================================

-- Public read access to standards for published zones
CREATE POLICY "Public standards read access" ON standards
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM zones z 
            WHERE z.id = standards.zone_id 
            AND z.published = true 
            AND z.is_current = true
        )
    );

-- Admin full access to standards
CREATE POLICY "Admin standards full access" ON standards
    FOR ALL
    TO zone_admin
    USING (true)
    WITH CHECK (true);

-- Worker can insert, update, and delete standards
CREATE POLICY "Worker standards write access" ON standards
    FOR INSERT
    TO zone_worker
    WITH CHECK (true);

CREATE POLICY "Worker standards update access" ON standards
    FOR UPDATE
    TO zone_worker
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Worker standards delete access" ON standards
    FOR DELETE
    TO zone_worker
    USING (true);

-- Worker can read all standards
CREATE POLICY "Worker standards read access" ON standards
    FOR SELECT
    TO zone_worker
    USING (true);

-- =============================================================================
-- INGESTION_JOBS TABLE POLICIES
-- =============================================================================

-- Admin full access to ingestion jobs
CREATE POLICY "Admin jobs full access" ON ingestion_jobs
    FOR ALL
    TO zone_admin
    USING (true)
    WITH CHECK (true);

-- Worker can read and update ingestion jobs
CREATE POLICY "Worker jobs read access" ON ingestion_jobs
    FOR SELECT
    TO zone_worker
    USING (true);

CREATE POLICY "Worker jobs update access" ON ingestion_jobs
    FOR UPDATE
    TO zone_worker
    USING (true)
    WITH CHECK (true);

-- Public users cannot access ingestion jobs
-- (No public policy means no access)

-- =============================================================================
-- FUNCTION PERMISSIONS
-- =============================================================================

-- Grant execute permissions on RPC functions

-- Public can execute search functions
GRANT EXECUTE ON FUNCTION search_zones(text) TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_zone_details(integer) TO PUBLIC;

-- Admin can execute all functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO zone_admin;

-- Worker can execute ingestion and job management functions
GRANT EXECUTE ON FUNCTION admin_ingest_zone(text, text, text, text, text, text, jsonb) TO zone_worker;
GRANT EXECUTE ON FUNCTION get_standard_value(jsonb, text) TO zone_worker;
GRANT EXECUTE ON FUNCTION update_ingestion_job(integer, text, text) TO zone_worker;
GRANT EXECUTE ON FUNCTION get_pending_jobs() TO zone_worker;

-- Grant table permissions to roles
GRANT SELECT ON zones TO zone_reader;
GRANT SELECT ON standards TO zone_reader;

GRANT ALL ON zones TO zone_admin;
GRANT ALL ON standards TO zone_admin;
GRANT ALL ON ingestion_jobs TO zone_admin;

GRANT SELECT, INSERT, UPDATE ON zones TO zone_worker;
GRANT SELECT, INSERT, UPDATE, DELETE ON standards TO zone_worker;
GRANT SELECT, UPDATE ON ingestion_jobs TO zone_worker;

-- =============================================================================
-- HELPER POLICIES FOR ANONYMOUS ACCESS
-- =============================================================================

-- Create a policy that allows anonymous users to access published data
-- This is important for the React app's public searches

CREATE POLICY "Anonymous read published zones" ON zones
    FOR SELECT
    TO anon
    USING (published = true AND is_current = true);

CREATE POLICY "Anonymous read published standards" ON standards
    FOR SELECT
    TO anon
    USING (
        EXISTS (
            SELECT 1 FROM zones z 
            WHERE z.id = standards.zone_id 
            AND z.published = true 
            AND z.is_current = true
        )
    );

-- Grant anonymous access to search functions
GRANT EXECUTE ON FUNCTION search_zones(text) TO anon;
GRANT EXECUTE ON FUNCTION get_zone_details(integer) TO anon;

-- =============================================================================
-- AUTHENTICATED USER POLICIES
-- =============================================================================

-- Authenticated users get the same access as anonymous for now
-- You can extend this later for user-specific features

CREATE POLICY "Authenticated read published zones" ON zones
    FOR SELECT
    TO authenticated
    USING (published = true AND is_current = true);

CREATE POLICY "Authenticated read published standards" ON standards
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM zones z 
            WHERE z.id = standards.zone_id 
            AND z.published = true 
            AND z.is_current = true
        )
    );

GRANT EXECUTE ON FUNCTION search_zones(text) TO authenticated;
GRANT EXECUTE ON FUNCTION get_zone_details(integer) TO authenticated;