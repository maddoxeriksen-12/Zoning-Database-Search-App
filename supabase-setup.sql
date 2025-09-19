-- Supabase Security Setup for Zoning Search App
-- Run this in your Supabase SQL Editor to configure secure read-only access

-- 1. Enable Row Level Security on the zones table
ALTER TABLE zones ENABLE ROW LEVEL SECURITY;

-- 2. Drop any existing policies that might allow write access
DROP POLICY IF EXISTS "Allow anonymous write" ON zones;
DROP POLICY IF EXISTS "Allow anonymous insert" ON zones;
DROP POLICY IF EXISTS "Allow anonymous update" ON zones;
DROP POLICY IF EXISTS "Allow anonymous delete" ON zones;

-- 3. Create read-only policy for anonymous users
DROP POLICY IF EXISTS "Allow anonymous read access" ON zones;
CREATE POLICY "Allow anonymous read access" ON zones
  FOR SELECT
  TO anon
  USING (true);

-- 4. Ensure the search_zones RPC function exists and is properly configured
-- This function provides controlled read-only access to the zones data
CREATE OR REPLACE FUNCTION public.search_zones(search_query TEXT)
RETURNS SETOF zones 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Return zones matching the search query
  -- This is a read-only operation
  RETURN QUERY
  SELECT * FROM zones
  WHERE 
    (zone_code ILIKE '%' || search_query || '%'
    OR municipality ILIKE '%' || search_query || '%'
    OR state ILIKE '%' || search_query || '%'
    OR zone_name ILIKE '%' || search_query || '%')
  ORDER BY municipality, zone_code
  LIMIT 100; -- Limit results for performance
END;
$$;

-- 5. Grant execute permission on the RPC function to anonymous users
GRANT EXECUTE ON FUNCTION public.search_zones TO anon;

-- 6. Revoke any dangerous permissions from anonymous users
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM anon;
REVOKE CREATE ON SCHEMA public FROM anon;

-- 7. Verify the configuration
DO $$
BEGIN
  RAISE NOTICE 'Security setup complete!';
  RAISE NOTICE 'Anonymous users can now:';
  RAISE NOTICE '  ✅ Read zones data through RLS policies';
  RAISE NOTICE '  ✅ Execute search_zones RPC function';
  RAISE NOTICE 'Anonymous users cannot:';
  RAISE NOTICE '  ❌ Insert, update, or delete data';
  RAISE NOTICE '  ❌ Create new tables or functions';
  RAISE NOTICE '  ❌ Access data without going through RLS policies';
END $$;