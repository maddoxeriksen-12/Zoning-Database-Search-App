# 🏠 Zoning Database Search Application

A comprehensive system for searching and displaying municipal zoning information with React frontend and complete data processing capabilities.

## 📥 Download & Installation

### Option 1: Clone the Repository
```bash
# Clone the repository
git clone https://github.com/maddoxeriksen-12/Zoning-Database-Search-App.git

# Navigate to the project directory
cd Zoning-Database-Search-App

# Go to the V2 application folder
cd Zoning-Search-App-PublicV2
```

### Option 2: Download ZIP
1. Go to: https://github.com/maddoxeriksen-12/Zoning-Database-Search-App
2. Click the green "Code" button
3. Select "Download ZIP"
4. Extract the ZIP file
5. Navigate to `Zoning-Search-App-PublicV2/` folder

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Start the application:**
   ```bash
   npm run docker:up
   ```

2. **Open your browser:**
   ```
   http://localhost:3000
   ```

3. **Stop the application:**
   ```bash
   npm run docker:down
   ```

### Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open in browser:**
   ```
   http://localhost:5173
   ```

## ✨ Features

### 🔍 Smart Search Capabilities
- **Partial Zone Matching**: Search "R-15" to find all R-15 variants
- **Municipality Search**: Search by town name to see all zones
- **Multi-Strategy Search**: Comprehensive search using multiple approaches
- **Natural Language**: Handles complex searches like "R-15 Middletown NJ"

### 📋 Detailed Zone Information
- **Zone Requirements**: Shows minimum area, frontage, depth, and coverage
- **Location Details**: Municipality, county, and state information
- **Ordinance Links**: Direct links to official zoning ordinances
- **Professional Layout**: Clean, easy-to-read zone cards

## 📖 Search Examples

| Search Query | Results |
|--------------|---------|
| `R-15 Middletown NJ` | All R-15 zones in Middletown, NJ |
| `Brick` | All zones in Brick township |
| `R-22` | R-22, R-22A, R-22B across all locations |
| `B-1 Ocean County` | B-1 zones in Ocean County |

## 🏗️ System Components

### 1. React Search App (V2)
- **Location**: `/Zoning-Search-App-PublicV2`
- **Tech Stack**: React 19, Vite, Supabase
- **Features**: Smart search, responsive UI, Docker deployment

### 2. Zoning Worker (Backend)
- **Location**: `/zoning-worker`
- **Purpose**: PDF processing and data extraction
- **Tech Stack**: Python, Docker, OCR capabilities

### 3. Database
- **Type**: Supabase PostgreSQL
- **Features**: Row Level Security, optimized search functions
- **Access**: Read-only public access configured

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the V2 app directory:
```bash
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_key
```

### Docker Configuration
- **Port**: 3000
- **Base Image**: Node.js 18 Alpine
- **Web Server**: Nginx
- **Build Type**: Multi-stage production build

## 📊 Database Schema

The system uses a comprehensive database with:
- **zones**: Core zoning information
- **standards**: Dimensional requirements
- **ingestion_jobs**: PDF processing tracking
- **Search Functions**: Optimized RPC functions for fast queries

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Docker Deployment
```bash
# Build and start
docker-compose up --build -d

# Scale if needed
docker-compose up --scale zoning-search-app=3
```

### GitHub Pages
```bash
npm run deploy
```

## 🛠️ Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run docker:up` - Start Docker containers
- `npm run docker:down` - Stop Docker containers

## 🔒 Security

- **Read-only database access**: Cannot modify data
- **Row Level Security**: Data protection enabled
- **Safe credentials**: Anonymous key only (no write access)
- **Public deployment ready**: Secure by default

## 📄 License

This project is configured for public use with read-only database access.

---

**Version 2.0** - Complete zoning search application with advanced capabilities