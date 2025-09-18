# 🏠 Zoning Search App

A modern React application for searching zoning information by zone code, municipality, and state. Built with Vite, React, and Supabase.

## ✨ Features

- **Smart Search Parsing**: Automatically extracts zone codes, municipalities, counties, and states from natural language input
- **Input Suggestions**: Provides helpful search suggestions as you type
- **Disambiguation Logic**: Prompts for missing information when searches are ambiguous
- **Dual Display Modes**: View results as clean cards or raw JSON data
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Search**: Powered by Supabase RPC calls for fast results

## 🔍 Search Examples

- `"R-20 Brick NJ"` - Find R-20 zones in Brick Township, New Jersey
- `"B-1 Middletown"` - Find B-1 zones in Middletown (will prompt for state)
- `"Ocean County M-1"` - Find M-1 zones in Ocean County
- `"VZ Township NJ"` - Find VZ zones in townships across New Jersey

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ installed
- Supabase project with zoning data

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd zoning-search-app
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Supabase configuration:
   ```
   VITE_SUPABASE_URL=your-supabase-url-here
   VITE_SUPABASE_ANON_KEY=your-supabase-anon-key-here
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

5. **Open in browser**
   Navigate to `http://localhost:5173`

## 🌐 Deployment to GitHub Pages

### Quick Deploy

```bash
npm run deploy
```

### Manual Setup

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Enable GitHub Pages**
   - Go to Repository Settings > Pages
   - Source: Deploy from a branch
   - Branch: gh-pages

## 📊 Supabase Setup

The app requires a `search_zones` RPC function in your Supabase database:

```sql
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
  depth_interior_lots_ft numeric,
  max_building_coverage_percent numeric
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    z.zone_code,
    z.zone_name,
    z.municipality,
    z.county,
    z.state,
    z.ordinance_url,
    s.area_sqft_interior_lots,
    s.frontage_interior_lots,
    s.depth_interior_lots_ft,
    s.max_building_coverage_percent
  FROM zones z
  LEFT JOIN standards s ON z.id = s.zone_id
  WHERE 
    search_query ILIKE '%' || z.zone_code || '%'
    OR search_query ILIKE '%' || z.municipality || '%'
    OR search_query ILIKE '%' || z.county || '%'
    OR search_query ILIKE '%' || z.state || '%'
  ORDER BY z.zone_code;
END;
$$;
```

## 🛠️ Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
