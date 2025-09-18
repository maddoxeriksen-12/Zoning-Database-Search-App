-- Sample Data for Zoning Worker
-- This file inserts sample data to test the system

-- Insert sample ingestion jobs
INSERT INTO ingestion_jobs (source_url, state_code, county, municipality, status, message) VALUES
('https://example.com/brick-zoning.pdf', 'NJ', 'Ocean County', 'Brick Township', 'DONE', 'Ingested 18/18 zones (failed: 0); best_conf=0.68'),
('https://example.com/middletown-zoning.pdf', 'NJ', 'Monmouth County', 'Middletown', 'DONE', 'Ingested 25/25 zones (failed: 0); best_conf=0.75'),
('https://example.com/toms-river-zoning.pdf', 'NJ', 'Ocean County', 'Toms River', 'PENDING', NULL);

-- Insert sample zones
INSERT INTO zones (state_code, county, municipality, zone_code, zone_name, ordinance_url, zone_key, municipality_id) VALUES
('NJ', 'Ocean County', 'Brick Township', 'R-R', 'Rural Residential', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|R-R', 1),
('NJ', 'Ocean County', 'Brick Township', 'R-20', 'Single Family Residential 20,000', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|R-20', 1),
('NJ', 'Ocean County', 'Brick Township', 'R-15', 'Single Family Residential 15,000', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|R-15', 1),
('NJ', 'Ocean County', 'Brick Township', 'R-10', 'Single Family Residential 10,000', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|R-10', 1),
('NJ', 'Ocean County', 'Brick Township', 'R-7.5', 'Single Family Residential 7,500', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|R-7.5', 1),
('NJ', 'Ocean County', 'Brick Township', 'B-1', 'Neighborhood Business', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|B-1', 1),
('NJ', 'Ocean County', 'Brick Township', 'B-2', 'General Business', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|B-2', 1),
('NJ', 'Ocean County', 'Brick Township', 'M-1', 'Light Industrial', 'https://example.com/brick-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|M-1', 1),
('NJ', 'Monmouth County', 'Middletown', 'R-15', 'Residential 15,000', 'https://example.com/middletown-zoning.pdf', 'NJ|MONMOUTH COUNTY|MIDDLETOWN|R-15', 2),
('NJ', 'Monmouth County', 'Middletown', 'R-10', 'Residential 10,000', 'https://example.com/middletown-zoning.pdf', 'NJ|MONMOUTH COUNTY|MIDDLETOWN|R-10', 2),
('NJ', 'Monmouth County', 'Middletown', 'B-1', 'Local Business', 'https://example.com/middletown-zoning.pdf', 'NJ|MONMOUTH COUNTY|MIDDLETOWN|B-1', 2),
('NJ', 'Monmouth County', 'Middletown', 'I-1', 'Light Industrial', 'https://example.com/middletown-zoning.pdf', 'NJ|MONMOUTH COUNTY|MIDDLETOWN|I-1', 2);

-- Insert sample standards for Brick Township zones
INSERT INTO standards (
    zone_id, zone_code, all_standards,
    area_sqft_interior_lots, frontage_interior_lots, area_sqft_corner_lots, frontage_feet_corner_lots,
    depth_interior_lots_ft, depth_corner_lots_ft,
    front_yard_principal_building, side_yard_principal_building, rear_yard_principal_building,
    max_building_coverage_percent, max_lot_coverage_percent,
    stories_max_height_principal_building, feet_max_height_principal_building
) VALUES
-- R-R Zone
(
    (SELECT id FROM zones WHERE zone_code = 'R-R' AND municipality = 'Brick Township'),
    'R-R',
    '[
        {"key": "area_interior_lots", "value_numeric": 87120, "units": "sq ft"},
        {"key": "frontage_interior_lots", "value_numeric": 200, "units": "ft"},
        {"key": "depth_interior_lots", "value_numeric": 200, "units": "ft"},
        {"key": "depth_corner_lots", "value_numeric": 175, "units": "ft"},
        {"key": "front_yard_principal", "value_numeric": 50, "units": "ft"},
        {"key": "side_yard_principal", "value_numeric": 25, "units": "ft"},
        {"key": "rear_yard_principal", "value_numeric": 50, "units": "ft"},
        {"key": "max_building_coverage", "value_numeric": 15, "units": "%"},
        {"key": "stories_max_height", "value_numeric": 2.5, "units": "stories"},
        {"key": "feet_max_height", "value_numeric": 35, "units": "ft"}
    ]'::jsonb,
    87120, 200, 100000, 250, 200, 175, 50, 25, 50, 15, 25, 2.5, 35
),
-- R-20 Zone
(
    (SELECT id FROM zones WHERE zone_code = 'R-20' AND municipality = 'Brick Township'),
    'R-20',
    '[
        {"key": "area_interior_lots", "value_numeric": 20000, "units": "sq ft"},
        {"key": "frontage_interior_lots", "value_numeric": 100, "units": "ft"},
        {"key": "depth_interior_lots", "value_numeric": 150, "units": "ft"},
        {"key": "depth_corner_lots", "value_numeric": 125, "units": "ft"},
        {"key": "front_yard_principal", "value_numeric": 30, "units": "ft"},
        {"key": "side_yard_principal", "value_numeric": 15, "units": "ft"},
        {"key": "rear_yard_principal", "value_numeric": 30, "units": "ft"},
        {"key": "max_building_coverage", "value_numeric": 25, "units": "%"},
        {"key": "stories_max_height", "value_numeric": 2.5, "units": "stories"},
        {"key": "feet_max_height", "value_numeric": 35, "units": "ft"}
    ]'::jsonb,
    20000, 100, 25000, 125, 150, 125, 30, 15, 30, 25, 35, 2.5, 35
),
-- R-15 Zone
(
    (SELECT id FROM zones WHERE zone_code = 'R-15' AND municipality = 'Brick Township'),
    'R-15',
    '[
        {"key": "area_interior_lots", "value_numeric": 15000, "units": "sq ft"},
        {"key": "frontage_interior_lots", "value_numeric": 85, "units": "ft"},
        {"key": "depth_interior_lots", "value_numeric": 125, "units": "ft"},
        {"key": "depth_corner_lots", "value_numeric": 110, "units": "ft"},
        {"key": "front_yard_principal", "value_numeric": 25, "units": "ft"},
        {"key": "side_yard_principal", "value_numeric": 12, "units": "ft"},
        {"key": "rear_yard_principal", "value_numeric": 25, "units": "ft"},
        {"key": "max_building_coverage", "value_numeric": 30, "units": "%"}
    ]'::jsonb,
    15000, 85, 18000, 100, 125, 110, 25, 12, 25, 30, 40, 2.5, 35
),
-- B-1 Zone
(
    (SELECT id FROM zones WHERE zone_code = 'B-1' AND municipality = 'Brick Township'),
    'B-1',
    '[
        {"key": "area_interior_lots", "value_numeric": 10000, "units": "sq ft"},
        {"key": "frontage_interior_lots", "value_numeric": 75, "units": "ft"},
        {"key": "front_yard_principal", "value_numeric": 25, "units": "ft"},
        {"key": "side_yard_principal", "value_numeric": 10, "units": "ft"},
        {"key": "rear_yard_principal", "value_numeric": 20, "units": "ft"},
        {"key": "max_building_coverage", "value_numeric": 50, "units": "%"},
        {"key": "stories_max_height", "value_numeric": 3, "units": "stories"},
        {"key": "feet_max_height", "value_numeric": 45, "units": "ft"}
    ]'::jsonb,
    10000, 75, 12000, 90, NULL, NULL, 25, 10, 20, 50, 60, 3, 45
);

-- Insert sample standards for Middletown zones
INSERT INTO standards (
    zone_id, zone_code, all_standards,
    area_sqft_interior_lots, frontage_interior_lots,
    depth_interior_lots_ft, depth_corner_lots_ft,
    front_yard_principal_building, side_yard_principal_building, rear_yard_principal_building,
    max_building_coverage_percent
) VALUES
-- Middletown R-15
(
    (SELECT id FROM zones WHERE zone_code = 'R-15' AND municipality = 'Middletown'),
    'R-15',
    '[
        {"key": "area_interior_lots", "value_numeric": 15000, "units": "sq ft"},
        {"key": "frontage_interior_lots", "value_numeric": 90, "units": "ft"},
        {"key": "depth_interior_lots", "value_numeric": 130, "units": "ft"},
        {"key": "depth_corner_lots", "value_numeric": 115, "units": "ft"},
        {"key": "front_yard_principal", "value_numeric": 30, "units": "ft"},
        {"key": "side_yard_principal", "value_numeric": 15, "units": "ft"},
        {"key": "rear_yard_principal", "value_numeric": 25, "units": "ft"},
        {"key": "max_building_coverage", "value_numeric": 25, "units": "%"}
    ]'::jsonb,
    15000, 90, 130, 115, 30, 15, 25, 25
),
-- Middletown B-1
(
    (SELECT id FROM zones WHERE zone_code = 'B-1' AND municipality = 'Middletown'),
    'B-1',
    '[
        {"key": "area_interior_lots", "value_numeric": 8000, "units": "sq ft"},
        {"key": "frontage_interior_lots", "value_numeric": 60, "units": "ft"},
        {"key": "front_yard_principal", "value_numeric": 20, "units": "ft"},
        {"key": "side_yard_principal", "value_numeric": 8, "units": "ft"},
        {"key": "rear_yard_principal", "value_numeric": 15, "units": "ft"},
        {"key": "max_building_coverage", "value_numeric": 60, "units": "%"}
    ]'::jsonb,
    8000, 60, NULL, NULL, 20, 8, 15, 60
);

-- Insert a test zone for demonstrating depth measurements
INSERT INTO zones (state_code, county, municipality, zone_code, zone_name, ordinance_url, zone_key, municipality_id) VALUES
('NJ', 'Ocean County', 'Brick Township', 'R-TEST', 'Test Residential Zone', 'https://example.com/test-zoning.pdf', 'NJ|OCEAN COUNTY|BRICK TOWNSHIP|R-TEST', 1);

INSERT INTO standards (
    zone_id, zone_code, all_standards,
    area_sqft_interior_lots, frontage_interior_lots,
    depth_interior_lots_ft, depth_corner_lots_ft,
    front_yard_principal_building, side_yard_principal_building, rear_yard_principal_building,
    max_building_coverage_percent
) VALUES
(
    (SELECT id FROM zones WHERE zone_code = 'R-TEST' AND municipality = 'Brick Township'),
    'R-TEST',
    '[
        {"key": "area_interior_lots", "value_numeric": 40000, "units": "sq ft"},
        {"key": "depth_interior_lots", "value_numeric": 150.0, "units": "ft"},
        {"key": "depth_corner_lots", "value_numeric": 125.0, "units": "ft"},
        {"key": "frontage_interior_lots", "value_numeric": 200, "units": "ft"},
        {"key": "front_yard_principal", "value_numeric": 35, "units": "ft"},
        {"key": "side_yard_principal", "value_numeric": 20, "units": "ft"},
        {"key": "rear_yard_principal", "value_numeric": 40, "units": "ft"},
        {"key": "max_building_coverage", "value_numeric": 20, "units": "%"}
    ]'::jsonb,
    40000, 200, 150.0, 125.0, 35, 20, 40, 20
);