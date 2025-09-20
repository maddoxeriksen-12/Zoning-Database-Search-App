-- RPC Functions for Zoning Worker
-- These functions provide the API interface for the React app and worker processes

-- Function to search zones (used by React app)
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
SECURITY DEFINER -- Run with elevated privileges
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
        -- Prioritize exact zone code matches
        CASE WHEN UPPER(z.zone_code) = UPPER(TRIM(search_query)) THEN 1 ELSE 2 END,
        -- Then by zone code similarity
        z.zone_code,
        z.municipality;
END;
$$;

-- Function to get zone details by ID
CREATE OR REPLACE FUNCTION get_zone_details(zone_id integer)
RETURNS TABLE(
    zone_code text,
    zone_name text,
    municipality text,
    county text,
    state text,
    ordinance_url text,
    effective_date date,
    standards jsonb
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
        z.effective_date,
        s.all_standards as standards
    FROM zones z
    LEFT JOIN standards s ON z.id = s.zone_id
    WHERE z.id = zone_id
    AND z.is_current = true
    AND z.published = true;
END;
$$;

-- Function for admin zone ingestion (used by worker)
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
    v_standard jsonb;
    v_key text;
    v_value_numeric numeric;
    v_value_text text;
    v_units text;
BEGIN
    -- Create zone key for uniqueness
    v_zone_key := UPPER(p_state_code) || '|' || UPPER(COALESCE(p_county, '')) || '|' || UPPER(p_municipality) || '|' || UPPER(p_zone_code);
    
    -- Insert or update zone
    INSERT INTO zones (
        state_code, county, municipality, zone_code, zone_name, 
        ordinance_url, zone_key, municipality_id
    ) VALUES (
        UPPER(p_state_code), p_county, p_municipality, UPPER(p_zone_code), p_zone_name,
        p_ordinance_url, v_zone_key, 1 -- Default municipality_id
    )
    ON CONFLICT (zone_key) 
    DO UPDATE SET
        zone_name = EXCLUDED.zone_name,
        ordinance_url = EXCLUDED.ordinance_url,
        updated_at = NOW()
    RETURNING id INTO v_zone_id;
    
    -- Delete existing standards for this zone
    DELETE FROM standards WHERE zone_id = v_zone_id;
    
    -- Insert new standards
    INSERT INTO standards (
        zone_id,
        zone_code,
        all_standards,
        -- Extract specific fields from JSON
        area_sqft_interior_lots,
        frontage_interior_lots,
        area_sqft_corner_lots,
        frontage_feet_corner_lots,
        depth_interior_lots_ft,
        depth_corner_lots_ft,
        front_yard_principal_building,
        side_yard_principal_building,
        street_side_yard_principal_building,
        rear_yard_principal_building,
        street_rear_yard_principal_building,
        front_yard_accessory_building,
        side_yard_accessory_building,
        street_side_yard_accessory_building,
        rear_yard_accessory_building,
        street_rear_yard_accessory_building,
        max_building_coverage_percent,
        max_lot_coverage_percent,
        stories_max_height_principal_building,
        feet_max_height_principal_building,
        total_minimum_gross_floor_area,
        first_floor_multistory_min_gross_floor_area,
        max_gross_floor_area,
        maximum_far,
        maximum_density
    ) VALUES (
        v_zone_id,
        UPPER(p_zone_code),
        p_standards,
        -- Extract values using helper function
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

-- Helper function to extract standard values from JSON
CREATE OR REPLACE FUNCTION get_standard_value(standards_json jsonb, standard_key text)
RETURNS numeric
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    standard_item jsonb;
BEGIN
    -- Look for the standard in the JSON array
    FOR standard_item IN SELECT jsonb_array_elements(standards_json)
    LOOP
        IF standard_item->>'key' = standard_key THEN
            -- Return numeric value if present
            IF standard_item ? 'value_numeric' AND (standard_item->>'value_numeric') IS NOT NULL THEN
                RETURN (standard_item->>'value_numeric')::numeric;
            END IF;
        END IF;
    END LOOP;
    
    RETURN NULL;
END;
$$;

-- Function to update ingestion job status
CREATE OR REPLACE FUNCTION update_ingestion_job(
    job_id integer,
    new_status text,
    message text DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE ingestion_jobs 
    SET 
        status = new_status,
        message = COALESCE(update_ingestion_job.message, ingestion_jobs.message),
        updated_at = NOW()
    WHERE id = job_id;
END;
$$;

-- Function to get pending ingestion jobs
CREATE OR REPLACE FUNCTION get_pending_jobs()
RETURNS TABLE(
    id integer,
    source_url text,
    state_code text,
    county text,
    municipality text,
    created_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        j.id,
        j.source_url,
        j.state_code,
        j.county,
        j.municipality,
        j.created_at
    FROM ingestion_jobs j
    WHERE j.status = 'PENDING'
    ORDER BY j.created_at ASC
    LIMIT 10;
END;
$$;