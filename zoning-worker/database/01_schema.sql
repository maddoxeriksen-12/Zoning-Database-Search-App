-- Zoning Worker Database Schema
-- This file creates the core tables for the zoning data system

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
    municipality_id INTEGER, -- For compatibility, can be derived from municipality name
    zone_code TEXT NOT NULL,
    zone_name TEXT,
    zone_key TEXT UNIQUE, -- Format: "STATE|COUNTY|MUNICIPALITY|ZONE_CODE"
    ordinance_url TEXT,
    effective_date DATE DEFAULT CURRENT_DATE,
    last_verified_at DATE DEFAULT CURRENT_DATE,
    is_current BOOLEAN DEFAULT TRUE,
    published BOOLEAN DEFAULT TRUE,
    
    -- Location fields
    state_code VARCHAR(2) NOT NULL,
    county TEXT,
    municipality TEXT NOT NULL,
    
    -- Indexes for fast searching
    CONSTRAINT zones_unique_location UNIQUE (state_code, county, municipality, zone_code)
);

-- Create standards table with all zoning standards
CREATE TABLE standards (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    
    -- Store original JSON for flexibility
    all_standards JSONB,
    
    -- Individual standard fields for easy querying
    area_sqft_interior_lots NUMERIC,
    frontage_interior_lots NUMERIC,
    area_sqft_corner_lots NUMERIC,
    frontage_feet_corner_lots NUMERIC,
    buildable_lot_area NUMERIC,
    
    -- Setback requirements - Principal Building
    front_yard_principal_building NUMERIC,
    side_yard_principal_building NUMERIC,
    street_side_yard_principal_building NUMERIC,
    rear_yard_principal_building NUMERIC,
    street_rear_yard_principal_building NUMERIC,
    
    -- Setback requirements - Accessory Building
    front_yard_accessory_building NUMERIC,
    side_yard_accessory_building NUMERIC,
    street_side_yard_accessory_building NUMERIC,
    rear_yard_accessory_building NUMERIC,
    street_rear_yard_accessory_building NUMERIC,
    
    -- Coverage and density
    max_building_coverage_percent NUMERIC,
    max_lot_coverage_percent NUMERIC,
    
    -- Height restrictions
    stories_max_height_principal_building NUMERIC,
    feet_max_height_principal_building NUMERIC,
    
    -- Floor area requirements
    total_minimum_gross_floor_area NUMERIC,
    first_floor_multistory_min_gross_floor_area NUMERIC,
    max_gross_floor_area NUMERIC,
    
    -- Development standards
    maximum_far NUMERIC,
    maximum_density NUMERIC,
    
    -- Depth measurements (NEW FIELDS)
    depth_interior_lots_ft NUMERIC,
    depth_corner_lots_ft NUMERIC,
    
    -- Duplicate zone_code for easier queries (denormalized)
    zone_code TEXT,
    
    -- Metadata
    key TEXT, -- For legacy compatibility
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
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

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_zones_updated_at BEFORE UPDATE ON zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_standards_updated_at BEFORE UPDATE ON standards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ingestion_jobs_updated_at BEFORE UPDATE ON ingestion_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();