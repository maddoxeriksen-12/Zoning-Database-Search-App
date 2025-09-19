# Security Configuration Guide

## Overview
This app is designed to provide **read-only** access to your Supabase zoning database. It uses Supabase's built-in security features to ensure your data remains protected.

## How It Works

### 1. Anon Key (Safe to Share)
The app uses your Supabase **anon key**, which is:
- **Public by design** - Safe to include in client-side code
- **Read-only by default** - Cannot modify data without explicit RLS policies
- **Required for access** - Users need this to connect to your database

### 2. Row Level Security (RLS)
Your database is protected by Row Level Security policies that:
- Control what data can be accessed
- Prevent unauthorized modifications
- Work automatically with the anon key

### 3. RPC Function
The app only uses the `search_zones` RPC function which:
- Is a read-only stored procedure
- Cannot modify, delete, or insert data
- Only returns search results

## Setting Up Your Supabase Project

### Step 1: Enable RLS on Your Tables

```sql
-- Enable RLS on your zones table
ALTER TABLE zones ENABLE ROW LEVEL SECURITY;

-- Create a read-only policy for anonymous users
CREATE POLICY "Allow anonymous read access" ON zones
  FOR SELECT
  TO anon
  USING (true);
```

### Step 2: Create the Search RPC Function

```sql
CREATE OR REPLACE FUNCTION search_zones(search_query TEXT)
RETURNS SETOF zones AS $$
BEGIN
  -- Your search logic here
  -- This function can only SELECT data, not modify it
  RETURN QUERY
  SELECT * FROM zones
  WHERE 
    zone_code ILIKE '%' || search_query || '%'
    OR municipality ILIKE '%' || search_query || '%'
    OR state ILIKE '%' || search_query || '%';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to anonymous users
GRANT EXECUTE ON FUNCTION search_zones TO anon;
```

### Step 3: Verify Security Settings

1. Go to your Supabase Dashboard
2. Navigate to Authentication > Policies
3. Ensure RLS is enabled on all tables
4. Verify that anonymous users only have SELECT permissions

## What Users CANNOT Do

With this configuration, users **cannot**:
- ❌ Insert new records
- ❌ Update existing records
- ❌ Delete any data
- ❌ Access your service key
- ❌ Modify database schema
- ❌ Access other projects or tables
- ❌ Execute arbitrary SQL

## What Users CAN Do

Users **can only**:
- ✅ Search for zoning information
- ✅ View search results
- ✅ Access data you've explicitly made public

## Adding Your Credentials

1. Get your credentials from Supabase Dashboard:
   - Project URL: `https://[PROJECT_ID].supabase.co`
   - Anon Key: Found in Settings > API > Project API keys > anon/public

2. Update `src/lib/supabase.js`:
   ```javascript
   const supabaseUrl = 'https://your-project.supabase.co'
   const supabaseKey = 'your-anon-key-here'
   ```

3. Or use environment variables (optional):
   ```bash
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key-here
   ```

## Security Checklist

Before making your app public, ensure:

- [ ] RLS is enabled on all tables
- [ ] Only SELECT policies exist for anonymous users
- [ ] The search_zones RPC function is read-only
- [ ] You're using the anon key, not the service key
- [ ] No sensitive data is exposed in search results
- [ ] Rate limiting is configured in Supabase Dashboard

## Additional Security Measures

### Rate Limiting
Configure rate limiting in Supabase Dashboard:
- Go to Settings > API
- Set appropriate rate limits for anonymous users

### Monitoring
Monitor usage in Supabase Dashboard:
- Check Database > Query Performance
- Review Authentication > Logs
- Set up alerts for unusual activity

## Questions?

If you're unsure about security:
1. Test with a separate Supabase project first
2. Review Supabase's security documentation
3. Ensure all RLS policies are properly configured
4. Never share your service key (only the anon key)

Remember: The anon key is designed to be public. Your data is protected by Row Level Security, not by hiding the key.