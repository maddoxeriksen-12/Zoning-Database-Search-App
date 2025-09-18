-- Complete Database Setup Script for Zoning Worker
-- Run this single file to set up your entire Supabase database

-- =============================================================================
-- STEP 1: CREATE SCHEMA AND TABLES
-- =============================================================================

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS standards CASCADE;
DROP TABLE IF EXISTS zones CASCADE;
DROP TABLE IF EXISTS ingestion_jobs CASCADE;

-- Create ingestion_jobs table
CREATE TABLE ingestion_jobs (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    county TEXT NOT NULL,
    municipality TEXT NOT NULL,
    pdf_storage_path TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'DONE', 'FAILED')),
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create zones table
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    municipality_id INTEGER DEFAULT 1,
    zone_code TEXT NOT NULL,
    zone_name TEXT,
    zone_key TEXT UNIQUE,
    ordinance_url TEXT,
    effective_date DATE DEFAULT CURRENT_DATE,
    last_verified_at DATE DEFAULT CURRENT_DATE,
    is_current BOOLEAN DEFAULT TRUE,
    published BOOLEAN DEFAULT TRUE,
    state_code VARCHAR(2) NOT NULL,
    county TEXT,
    municipality TEXT NOT NULL,
    CONSTRAINT zones_unique_location UNIQUE (state_code, county, municipality, zone_code)
);

-- Create standards table
CREATE TABLE standards (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    all_standards JSONB,
    area_sqft_interior_lots NUMERIC,
    frontage_interior_lots NUMERIC,
    area_sqft_corner_lots NUMERIC,
    frontage_feet_corner_lots NUMERIC,
    buildable_lot_area NUMERIC,
    front_yard_principal_building NUMERIC,
    side_yard_principal_building NUMERIC,
    street_side_yard_principal_building NUMERIC,
    rear_yard_principal_building NUMERIC,
    street_rear_yard_principal_building NUMERIC,
    front_yard_accessory_building NUMERIC,
    side_yard_accessory_building NUMERIC,
    street_side_yard_accessory_building NUMERIC,
    rear_yard_accessory_building NUMERIC,
    street_rear_yard_accessory_building NUMERIC,
    max_building_coverage_percent NUMERIC,
    max_lot_coverage_percent NUMERIC,
    stories_max_height_principal_building NUMERIC,
    feet_max_height_principal_building NUMERIC,
    total_minimum_gross_floor_area NUMERIC,
    first_floor_multistory_min_gross_floor_area NUMERIC,
    max_gross_floor_area NUMERIC,
    maximum_far NUMERIC,
    maximum_density NUMERIC,
    depth_interior_lots_ft NUMERIC,
    depth_corner_lots_ft NUMERIC,
    zone_code TEXT,
    key TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_zones_state_municipality ON zones(state_code, municipality);
CREATE INDEX idx_zones_zone_code ON zones(zone_code);
CREATE INDEX idx_zones_municipality ON zones(municipality);
CREATE INDEX idx_zones_county ON zones(county);
CREATE INDEX idx_zones_zone_key ON zones(zone_key);
CREATE INDEX idx_standards_zone_id ON standards(zone_id);
CREATE INDEX idx_standards_zone_code ON standards(zone_code);
CREATE INDEX idx_standards_all_standards ON standards USING GIN(all_standards);
CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX idx_ingestion_jobs_municipality ON ingestion_jobs(municipality, state_code);

-- =============================================================================
-- STEP 2: CREATE FUNCTIONS
-- =============================================================================

-- Helper function to extract standard values from JSON
CREATE OR REPLACE FUNCTION get_standard_value(standards_json jsonb, standard_key text)
RETURNS numeric
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    standard_item jsonb;
BEGIN
    FOR standard_item IN SELECT jsonb_array_elements(standards_json)
    LOOP
        IF standard_item->>'key' = standard_key THEN
            IF standard_item ? 'value_numeric' AND (standard_item->>'value_numeric') IS NOT NULL THEN
                RETURN (standard_item->>'value_numeric')::numeric;
            END IF;
        END IF;
    END LOOP;
    RETURN NULL;
END;
$$;

-- Main search function for React app
CREATE OR REPLACE FUNCTION search_zones(search_query text)
RETURNS TABLE(
    zone_code text,
    zone_name text,
    municipality text,
    county text,
    state text,
    ordinance_url text,
    area_sqft_interior_lots numeric,
    frontage_interior_lots numeric,
    area_sqft_corner_lots numeric,
    frontage_feet_corner_lots numeric,
    depth_interior_lots_ft numeric,
    depth_corner_lots_ft numeric,
    max_building_coverage_percent numeric,
    max_lot_coverage_percent numeric,
    stories_max_height_principal_building numeric,
    feet_max_height_principal_building numeric,
    maximum_density numeric,
    maximum_far numeric
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        z.zone_code,
        z.zone_name,
        z.municipality,
        z.county,
        z.state_code as state,
        z.ordinance_url,
        s.area_sqft_interior_lots,
        s.frontage_interior_lots,
        s.area_sqft_corner_lots,
        s.frontage_feet_corner_lots,
        s.depth_interior_lots_ft,
        s.depth_corner_lots_ft,
        s.max_building_coverage_percent,
        s.max_lot_coverage_percent,
        s.stories_max_height_principal_building,
        s.feet_max_height_principal_building,
        s.maximum_density,
        s.maximum_far
    FROM zones z
    LEFT JOIN standards s ON z.id = s.zone_id
    WHERE 
        z.is_current = true
        AND z.published = true
        AND (
            search_query ILIKE '%' || z.zone_code || '%'
            OR search_query ILIKE '%' || z.municipality || '%'
            OR search_query ILIKE '%' || z.county || '%'
            OR search_query ILIKE '%' || z.state_code || '%'
            OR search_query ILIKE '%' || COALESCE(z.zone_name, '') || '%'
        )
    ORDER BY 
        CASE WHEN UPPER(z.zone_code) = UPPER(TRIM(search_query)) THEN 1 ELSE 2 END,
        z.zone_code,
        z.municipality;
END;
$$;

-- Admin ingestion function for worker
CREATE OR REPLACE FUNCTION admin_ingest_zone(
    p_state_code text,
    p_county text,
    p_municipality text,
    p_zone_code text,
    p_zone_name text DEFAULT NULL,
    p_ordinance_url text DEFAULT NULL,
    p_standards jsonb DEFAULT '{}'::jsonb
)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_zone_id integer;
    v_zone_key text;
BEGIN
    v_zone_key := UPPER(p_state_code) || '|' || UPPER(COALESCE(p_county, '')) || '|' || UPPER(p_municipality) || '|' || UPPER(p_zone_code);
    
    INSERT INTO zones (
        state_code, county, municipality, zone_code, zone_name, 
        ordinance_url, zone_key, municipality_id
    ) VALUES (
        UPPER(p_state_code), p_county, p_municipality, UPPER(p_zone_code), p_zone_name,
        p_ordinance_url, v_zone_key, 1
    )
    ON CONFLICT (zone_key) 
    DO UPDATE SET
        zone_name = EXCLUDED.zone_name,
        ordinance_url = EXCLUDED.ordinance_url,
        updated_at = NOW()
    RETURNING id INTO v_zone_id;
    
    DELETE FROM standards WHERE zone_id = v_zone_id;
    
    INSERT INTO standards (
        zone_id, zone_code, all_standards,
        area_sqft_interior_lots, frontage_interior_lots, area_sqft_corner_lots, frontage_feet_corner_lots,
        depth_interior_lots_ft, depth_corner_lots_ft, front_yard_principal_building, side_yard_principal_building,
        street_side_yard_principal_building, rear_yard_principal_building, street_rear_yard_principal_building,
        front_yard_accessory_building, side_yard_accessory_building, street_side_yard_accessory_building,
        rear_yard_accessory_building, street_rear_yard_accessory_building, max_building_coverage_percent,
        max_lot_coverage_percent, stories_max_height_principal_building, feet_max_height_principal_building,
        total_minimum_gross_floor_area, first_floor_multistory_min_gross_floor_area, max_gross_floor_area,
        maximum_far, maximum_density
    ) VALUES (
        v_zone_id, UPPER(p_zone_code), p_standards,
        (SELECT get_standard_value(p_standards, 'area_interior_lots')),
        (SELECT get_standard_value(p_standards, 'frontage_interior_lots')),
        (SELECT get_standard_value(p_standards, 'area_corner_lots')),
        (SELECT get_standard_value(p_standards, 'frontage_corner_lots')),
        (SELECT get_standard_value(p_standards, 'depth_interior_lots')),
        (SELECT get_standard_value(p_standards, 'depth_corner_lots')),
        (SELECT get_standard_value(p_standards, 'front_yard_principal')),
        (SELECT get_standard_value(p_standards, 'side_yard_principal')),
        (SELECT get_standard_value(p_standards, 'street_side_yard_principal')),
        (SELECT get_standard_value(p_standards, 'rear_yard_principal')),
        (SELECT get_standard_value(p_standards, 'street_rear_yard_principal')),
        (SELECT get_standard_value(p_standards, 'front_yard_accessory')),
        (SELECT get_standard_value(p_standards, 'side_yard_accessory')),
        (SELECT get_standard_value(p_standards, 'street_side_yard_accessory')),
        (SELECT get_standard_value(p_standards, 'rear_yard_accessory')),
        (SELECT get_standard_value(p_standards, 'street_rear_yard_accessory')),
        (SELECT get_standard_value(p_standards, 'max_building_coverage')),
        (SELECT get_standard_value(p_standards, 'max_lot_coverage')),
        (SELECT get_standard_value(p_standards, 'stories_max_height')),
        (SELECT get_standard_value(p_standards, 'feet_max_height')),
        (SELECT get_standard_value(p_standards, 'total_min_gross_floor_area')),
        (SELECT get_standard_value(p_standards, 'first_floor_multistory_min_gross_floor_area')),
        (SELECT get_standard_value(p_standards, 'max_gross_floor_area')),
        (SELECT get_standard_value(p_standards, 'maximum_far')),
        (SELECT get_standard_value(p_standards, 'maximum_density'))
    );
    
    RETURN v_zone_id;
END;
$$;

-- =============================================================================
-- STEP 3: ENABLE ROW LEVEL SECURITY
-- =============================================================================

ALTER TABLE zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE standards ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_jobs ENABLE ROW LEVEL SECURITY;

-- Public read access to published zones and standards
CREATE POLICY "Public zones access" ON zones FOR SELECT USING (published = true AND is_current = true);
CREATE POLICY "Public standards access" ON standards FOR SELECT USING (
    EXISTS (SELECT 1 FROM zones z WHERE z.id = standards.zone_id AND z.published = true AND z.is_current = true)
);

-- Anonymous access (for React app)
CREATE POLICY "Anonymous zones access" ON zones FOR SELECT TO anon USING (published = true AND is_current = true);
CREATE POLICY "Anonymous standards access" ON standards FOR SELECT TO anon USING (
    EXISTS (SELECT 1 FROM zones z WHERE z.id = standards.zone_id AND z.published = true AND z.is_current = true)
);

-- Authenticated user access
CREATE POLICY "Authenticated zones access" ON zones FOR SELECT TO authenticated USING (published = true AND is_current = true);
CREATE POLICY "Authenticated standards access" ON standards FOR SELECT TO authenticated USING (
    EXISTS (SELECT 1 FROM zones z WHERE z.id = standards.zone_id AND z.published = true AND z.is_current = true)
);

-- =============================================================================
-- STEP 4: GRANT PERMISSIONS
-- =============================================================================

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION search_zones(text) TO PUBLIC;
GRANT EXECUTE ON FUNCTION search_zones(text) TO anon;
GRANT EXECUTE ON FUNCTION search_zones(text) TO authenticated;

-- =============================================================================
-- STEP 5: INSERT SAMPLE DATA
-- =============================================================================

-- Sample zones
INSERT INTO zones (state_code, county, municipality, zone_code, zone_name, ordinance_url, zone_key) VALUES
('NJ', 'Ocean County', 'Brick Township', 'R-20', 'Single Family Residential 20,000', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|R-20'),
('NJ', 'Ocean County', 'Brick Township', 'R-15', 'Single Family Residential 15,000', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|R-15'),
('NJ', 'Ocean County', 'Brick Township', 'B-1', 'Neighborhood Business', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|B-1'),
('NJ', 'Monmouth County', 'Middletown', 'R-15', 'Residential 15,000', 'https://example.com/middletown-zoning.pdf', 'NJ|MONMOUTH COUNTY|MIDDLETOWN|R-15');

-- Sample standards with depth measurements
INSERT INTO standards (zone_id, zone_code, all_standards, area_sqft_interior_lots, frontage_interior_lots, depth_interior_lots_ft, depth_corner_lots_ft, max_building_coverage_percent) VALUES
(
    (SELECT id FROM zones WHERE zone_code = 'R-20' AND municipality = 'Brick Township'),
    'R-20',
    '[{"key": "area_interior_lots", "value_numeric": 20000, "units": "sq ft"}, {"key": "depth_interior_lots", "value_numeric": 150, "units": "ft"}, {"key": "depth_corner_lots", "value_numeric": 125, "units": "ft"}]'::jsonb,
    20000, 100, 150, 125, 25
),
(
    (SELECT id FROM zones WHERE zone_code = 'R-15' AND municipality = 'Brick Township'),
    'R-15',
    '[{"key": "area_interior_lots", "value_numeric": 15000, "units": "sq ft"}, {"key": "depth_interior_lots", "value_numeric": 125, "units": "ft"}, {"key": "depth_corner_lots", "value_numeric": 110, "units": "ft"}]'::jsonb,
    15000, 85, 125, 110, 30
);

-- =============================================================================
-- SETUP COMPLETE
-- =============================================================================

-- Verify setup with a test query
SELECT 'Database setup complete! Testing search function...' as status;
SELECT zone_code, municipality, depth_interior_lots_ft, depth_corner_lots_ft 
FROM search_zones('R-20 Brick') 
LIMIT 3;