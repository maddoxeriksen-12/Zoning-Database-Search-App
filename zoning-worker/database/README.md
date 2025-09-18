# 🗄️ Zoning Worker Database Setup

Complete SQL scripts to set up a Supabase database with Row Level Security (RLS) for the Zoning Worker system.

## 🚀 Quick Setup

### Option 1: Single File Setup (Recommended)
Run the complete setup with one file:
```sql
-- In Supabase SQL Editor, run:
\i setup.sql
```

### Option 2: Step-by-Step Setup
Run files in order:
1. `01_schema.sql` - Create tables and indexes
2. `02_rpc_functions.sql` - Create RPC functions for API
3. `03_rls_policies.sql` - Set up Row Level Security
4. `04_sample_data.sql` - Insert sample data for testing

## 📋 Database Schema

### Core Tables

#### `zones`
- **Purpose**: Store zoning district information
- **Key Fields**: `zone_code`, `municipality`, `county`, `state_code`, `ordinance_url`
- **Unique Constraint**: `(state_code, county, municipality, zone_code)`

#### `standards`
- **Purpose**: Store detailed zoning standards for each zone
- **Key Fields**: All zoning measurements (lot sizes, setbacks, heights, etc.)
- **Special Fields**: `depth_interior_lots_ft`, `depth_corner_lots_ft` (new depth measurements)
- **JSON Field**: `all_standards` stores original extracted data

#### `ingestion_jobs`
- **Purpose**: Track PDF processing jobs
- **Key Fields**: `source_url`, `status`, `municipality`, `message`
- **Statuses**: `PENDING`, `PROCESSING`, `DONE`, `FAILED`

## 🔐 Security Model

### Row Level Security (RLS)
All tables have RLS enabled with these access patterns:

#### **Public Access** (for React app)
- ✅ **Read** published zones and their standards
- ❌ **No write** access to any data
- ❌ **No access** to ingestion jobs

#### **Anonymous Users** (anon)
- ✅ Same as public access
- ✅ Can execute `search_zones()` function

#### **Authenticated Users** (authenticated)
- ✅ Same as anonymous users
- 🔮 **Extensible** for user-specific features

#### **Worker Role** (zone_worker)
- ✅ **Read/Write** zones and standards
- ✅ **Read/Update** ingestion jobs
- ✅ Can execute admin functions like `admin_ingest_zone()`

#### **Admin Role** (zone_admin)
- ✅ **Full access** to all tables and functions
- ✅ Can manage users and permissions

## 🔧 Key Functions

### `search_zones(search_query text)`
**Purpose**: Main search function for React app
**Returns**: Zone data with standards
**Example**:
```sql
SELECT * FROM search_zones('R-20 Brick NJ');
```

### `admin_ingest_zone(...)`
**Purpose**: Worker function to insert/update zones
**Parameters**: State, county, municipality, zone code, standards JSON
**Example**:
```sql
SELECT admin_ingest_zone(
    'NJ', 
    'Ocean County', 
    'Brick Township', 
    'R-TEST',
    'Test Zone',
    'https://example.com/zoning.pdf',
    '[{"key": "area_interior_lots", "value_numeric": 20000}]'::jsonb
);
```

### `get_standard_value(standards_json, key)`
**Purpose**: Extract specific values from standards JSON
**Example**:
```sql
SELECT get_standard_value(
    '[{"key": "depth_interior_lots", "value_numeric": 150}]'::jsonb,
    'depth_interior_lots'
); -- Returns: 150
```

## 📊 Sample Data

The setup includes sample data for:
- **Brick Township, NJ**: R-20, R-15, B-1 zones with depth measurements
- **Middletown, NJ**: R-15, B-1 zones
- **Test Zone**: R-TEST with comprehensive standards

## 🛠️ Setup Instructions

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Note your project URL and anon key

### 2. Run Database Setup
In Supabase SQL Editor:
```sql
-- Copy and paste the entire contents of setup.sql
-- Or run individual files in order
```

### 3. Verify Setup
Test the search function:
```sql
SELECT zone_code, municipality, depth_interior_lots_ft 
FROM search_zones('R-20') 
LIMIT 5;
```

### 4. Configure Environment
Update your React app's `.env`:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

## 🔍 Testing Queries

### Search Examples
```sql
-- Search by zone code
SELECT * FROM search_zones('R-20');

-- Search by municipality
SELECT * FROM search_zones('Brick');

-- Search by state
SELECT * FROM search_zones('NJ');

-- Combined search
SELECT * FROM search_zones('R-15 Middletown NJ');
```

### Depth Data Verification
```sql
-- Check zones with depth measurements
SELECT 
    zone_code, 
    municipality, 
    depth_interior_lots_ft, 
    depth_corner_lots_ft
FROM search_zones('NJ')
WHERE depth_interior_lots_ft IS NOT NULL
ORDER BY zone_code;
```

### Standards Analysis
```sql
-- Get zones with specific coverage limits
SELECT 
    zone_code, 
    municipality, 
    max_building_coverage_percent
FROM search_zones('NJ')
WHERE max_building_coverage_percent > 25
ORDER BY max_building_coverage_percent DESC;
```

## 🔒 Advanced Security

### Custom Roles
Create additional roles for specific use cases:

```sql
-- Create data analyst role (read-only access)
CREATE ROLE zone_analyst;
GRANT SELECT ON zones, standards TO zone_analyst;

-- Create municipality admin (limited write access)
CREATE ROLE municipality_admin;
GRANT SELECT, INSERT, UPDATE ON zones TO municipality_admin;
```

### Audit Logging
Add audit triggers for change tracking:

```sql
-- Create audit table
CREATE TABLE zone_audit (
    id SERIAL PRIMARY KEY,
    table_name TEXT,
    record_id INTEGER,
    operation TEXT,
    old_values JSONB,
    new_values JSONB,
    changed_by TEXT,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO zone_audit (table_name, record_id, operation, old_values, new_values, changed_by)
    VALUES (TG_TABLE_NAME, COALESCE(NEW.id, OLD.id), TG_OP, to_jsonb(OLD), to_jsonb(NEW), current_user);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER zones_audit AFTER INSERT OR UPDATE OR DELETE ON zones
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();
```

## 📈 Performance Optimization

### Additional Indexes
```sql
-- Full-text search index
CREATE INDEX idx_zones_fulltext ON zones 
USING GIN(to_tsvector('english', zone_code || ' ' || municipality || ' ' || COALESCE(county, '') || ' ' || state_code));

-- Composite search index
CREATE INDEX idx_zones_search ON zones(state_code, municipality, zone_code) 
WHERE published = true AND is_current = true;
```

### Query Optimization
```sql
-- Optimized search with ranking
CREATE OR REPLACE FUNCTION search_zones_ranked(search_query text)
RETURNS TABLE(zone_code text, municipality text, relevance numeric)
LANGUAGE sql
AS $$
    SELECT 
        z.zone_code,
        z.municipality,
        ts_rank(to_tsvector('english', z.zone_code || ' ' || z.municipality), plainto_tsquery('english', search_query)) as relevance
    FROM zones z
    WHERE to_tsvector('english', z.zone_code || ' ' || z.municipality) @@ plainto_tsquery('english', search_query)
    AND z.published = true AND z.is_current = true
    ORDER BY relevance DESC;
$$;
```

## 🆘 Troubleshooting

### Common Issues

**Permission Denied Errors**
```sql
-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename IN ('zones', 'standards');

-- Grant missing permissions
GRANT USAGE ON SCHEMA public TO anon;
GRANT EXECUTE ON FUNCTION search_zones(text) TO anon;
```

**Function Not Found**
```sql
-- Verify function exists
SELECT routine_name FROM information_schema.routines 
WHERE routine_schema = 'public' AND routine_name = 'search_zones';

-- Recreate if missing
\i 02_rpc_functions.sql
```

**No Search Results**
```sql
-- Check data exists
SELECT COUNT(*) FROM zones WHERE published = true;

-- Check RLS allows access
SET ROLE anon;
SELECT COUNT(*) FROM zones; -- Should return > 0
RESET ROLE;
```

## 📞 Support

For issues with the database setup:
1. Check Supabase logs in the dashboard
2. Verify RLS policies allow appropriate access
3. Test functions individually before integrating
4. Review sample data for expected format