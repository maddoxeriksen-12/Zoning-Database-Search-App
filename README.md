# 🏠 Zoning Worker - Complete Zoning Data Processing System

A comprehensive system for extracting, processing, and serving zoning information from municipal PDFs.

## 🚨 Security Notice

**IMPORTANT**: This repository contains sanitized code with placeholder credentials. To use this system:

1. **Never commit real credentials to git**
2. **Copy `.env.example` files to `.env` and add your own credentials**
3. **Set up your own Supabase project (see setup instructions below)**

## 🏗️ System Architecture

This system consists of three main components:

### 1. 🔄 Zoning Worker (`/zoning-worker`)
**Purpose**: Processes PDF documents to extract zoning information
- Docker-based Python worker
- Supabase integration for data storage
- OCR and text processing capabilities
- Automated PDF ingestion pipeline

### 2. 🗄️ Database Setup (`/database`)
**Purpose**: Complete Supabase database schema with Row Level Security
- PostgreSQL schema for zones, standards, and ingestion jobs
- RPC functions for API access
- Comprehensive Row Level Security policies
- Sample data for testing

### 3. 🌐 React Search App (`/zoning-search-app`)
**Purpose**: Public-facing search interface
- React + Vite frontend
- Supabase client integration
- Smart search with input parsing
- Clean UI with JSON and card displays
- GitHub Pages deployment ready

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for React app)
- Supabase account

### 1. Set Up Supabase Database

1. Create a new project at [supabase.com](https://supabase.com)
2. Run the database setup:
   ```sql
   -- In Supabase SQL Editor, run:
   \\i database/setup.sql
   ```
3. Note your project URL and keys from Settings > API

### 2. Configure Zoning Worker

1. Copy environment file:
   ```bash
   cd zoning-worker
   cp .env.example .env
   ```

2. Update `.env` with your Supabase credentials:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   POLL_INTERVAL_SECONDS=5
   BATCH_SIZE=1
   CONFIDENCE_THRESHOLD=0.90
   STORAGE_BUCKET=zoning-pdfs
   AUTO_INGEST=true
   ```

3. Start the worker:
   ```bash
   docker-compose up --build
   ```

### 3. Set Up React Search App

1. Copy environment file:
   ```bash
   cd zoning-search-app
   cp .env.example .env.local
   ```

2. Update `.env.local` with your Supabase credentials:
   ```env
   VITE_SUPABASE_URL=https://your-project-id.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key-here
   ```

3. Install and run:
   ```bash
   npm install
   npm run dev
   ```

4. Deploy to GitHub Pages:
   ```bash
   npm run deploy
   ```

## 📋 Features

### Zoning Worker Features
- ✅ **PDF Processing**: Extracts text and tables from zoning PDFs
- ✅ **OCR Support**: Handles scanned documents
- ✅ **Smart Parsing**: Identifies zoning codes, setbacks, lot sizes
- ✅ **Database Integration**: Stores extracted data in structured format
- ✅ **Depth Measurements**: Extracts lot depth requirements
- ✅ **Error Handling**: Robust processing with confidence scoring

### Database Features
- ✅ **Complete Schema**: Tables for zones, standards, ingestion jobs
- ✅ **Row Level Security**: Public read, admin write access
- ✅ **Search Functions**: Optimized RPC functions for frontend
- ✅ **Sample Data**: Ready-to-use test data included
- ✅ **Flexible Storage**: JSONB for extensible standards

### React App Features
- ✅ **Smart Search**: Parses natural language queries
- ✅ **Input Disambiguation**: Prompts for missing location info
- ✅ **Dual Display**: JSON view and clean card UI
- ✅ **Responsive Design**: Works on desktop and mobile
- ✅ **GitHub Pages Ready**: Single command deployment

## 🔧 Configuration

### Zoning Worker Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `POLL_INTERVAL_SECONDS` | How often to check for new jobs | 5 |
| `BATCH_SIZE` | Number of jobs to process at once | 1 |
| `CONFIDENCE_THRESHOLD` | Minimum confidence for extraction | 0.90 |
| `STORAGE_BUCKET` | Supabase storage bucket name | zoning-pdfs |
| `AUTO_INGEST` | Automatically process new jobs | true |

### Database Configuration

The database supports multiple user roles:
- **Public/Anonymous**: Read published zones only
- **Authenticated**: Same as anonymous (extensible)
- **zone_worker**: Read/write zones and standards
- **zone_admin**: Full access to all tables

### React App Configuration

Set these environment variables:
- `VITE_SUPABASE_URL`: Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key

## 📊 Usage Examples

### Search Examples
```
# Search by zone code
R-20

# Search by municipality
Brick Township NJ

# Combined search
R-15 Middletown NJ

# Partial matches work too
R-15 Middle
```

### Database Queries
```sql
-- Search zones
SELECT * FROM search_zones('R-20');

-- Get zones with depth measurements
SELECT zone_code, municipality, depth_interior_lots_ft 
FROM search_zones('NJ') 
WHERE depth_interior_lots_ft IS NOT NULL;

-- Check processing status
SELECT * FROM ingestion_jobs WHERE status = 'PENDING';
```

## 🛠️ Development

### Adding New Zoning Standards

1. Update the database schema in `database/01_schema.sql`
2. Modify the worker parser in `zoning-worker/worker/parsers.py`
3. Update the React UI components as needed

### Extending Search Functionality

1. Modify `search_zones()` function in `database/02_rpc_functions.sql`
2. Update React search components in `zoning-search-app/src/components/`

### Custom Deployment

- **Worker**: Modify `docker-compose.yml` for your deployment environment
- **Database**: SQL files work with any PostgreSQL 14+ instance
- **Frontend**: Vite supports deployment to any static hosting service

## 🆘 Troubleshooting

### Common Issues

**"Permission denied" errors**
```sql
-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'zones';

-- Grant missing permissions
GRANT EXECUTE ON FUNCTION search_zones(text) TO anon;
```

**No search results**
```sql
-- Verify data exists
SELECT COUNT(*) FROM zones WHERE published = true;

-- Test RLS access
SET ROLE anon;
SELECT COUNT(*) FROM zones;
RESET ROLE;
```

**Worker not processing**
- Check Docker logs: `docker-compose logs -f`
- Verify environment variables in `.env`
- Ensure Supabase credentials are correct

## 📞 Support

This is an open-source project. For issues:
1. Check the troubleshooting section above
2. Review the database and worker logs
3. Verify your Supabase configuration
4. Test with the sample data provided

## 📄 License

This project is open source. Use responsibly and ensure you comply with your municipality's data usage policies.

---

**Security Reminder**: Always use your own Supabase credentials. Never commit real API keys to version control.