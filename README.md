# Zoning Search App Public V2

## 🏠 Advanced Zoning Information Search Application

A sophisticated React-based web application for searching and displaying municipal zoning information with comprehensive zone matching capabilities.

## ✨ Features

### 🔍 **Smart Search Capabilities**
- **Partial Zone Matching**: Search "R-15" to find "R-15", "R-15A", "R-15 Nonconforming", etc.
- **Municipality-Only Search**: Search "Brick" to see all zones in that town
- **Multi-Strategy Search**: Comprehensive search using multiple approaches to find all relevant zones
- **Intelligent Parsing**: Handles complex searches like "R-15 Middletown NJ"

### 📋 **Detailed Zone Information**
- **Zone Requirements Display**: Shows minimum area, frontage, and buildable lot coverage
- **Location Details**: Municipality, county, and state information
- **Ordinance Links**: Direct links to official zoning ordinances when available
- **Professional Layout**: Clean, easy-to-read zone cards

### 🎯 **Advanced Matching**
- **Exact Matches**: Prioritizes exact zone code matches
- **Partial Matches**: Finds zones that start with your search term
- **Long Zone Names**: Handles complex zone codes like "R-15 Nonconforming 5,001 -10,000 SF lots"
- **Cross-Reference Search**: Uses multiple search strategies to ensure comprehensive results

## 🚀 Quick Start

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


### Using Docker (Recommended)

1. **Start the application:**
   ```bash
   npm run docker:up
   ```

2. **Open your browser:**
   ```
   http://localhost:3001
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

3. **Build for production:**
   ```bash
   npm run build
   ```

## 📖 How to Use

### Example Searches

| Search Query | Results |
|--------------|---------|
| `R-15 Middletown NJ` | All R-15 zones in Middletown, NJ |
| `Brick` | All zones in Brick township |
| `R-22` | R-22, R-22A, R-22B, etc. across all locations |
| `B-1 Ocean County` | B-1 zones in Ocean County |

### Search Tips

- **Include State**: Adding "NJ" helps narrow results
- **Municipality Names**: Works with multi-word names like "East Brunswick"
- **Partial Zone Codes**: "R-15" finds all R-15 variants
- **County Search**: Use "Ocean County" for county-wide results

## 🏗️ Architecture

### Frontend
- **React 19**: Modern React with latest features
- **Vite**: Fast build tool and development server
- **CSS Grid/Flexbox**: Responsive layout system

### Backend Integration
- **Supabase**: Real-time database with RPC functions
- **Multiple Search Strategies**: Comprehensive zone discovery
- **Smart Filtering**: Relevance-based result ranking

### Deployment
- **Docker**: Containerized deployment
- **Nginx**: Production-ready web server
- **Multi-stage Build**: Optimized for production

## 📁 Project Structure

```
Zoning-Search-App-PublicV2/
├── src/
│   ├── components/
│   │   └── ZoneSearch.jsx       # Main search component
│   ├── lib/
│   │   └── supabase.js          # Database connection
│   ├── utils/
│   │   └── searchParser.js      # Search logic utilities
│   ├── App.jsx                  # Root component
│   ├── App.css                  # Application styles
│   └── main.jsx                 # Application entry point
├── public/                      # Static assets
├── Dockerfile                   # Container configuration
├── docker-compose.yml           # Container orchestration
├── nginx.conf                   # Web server configuration
└── package.json                 # Dependencies and scripts
```

## 🔧 Configuration

### Environment Variables (Optional)
```bash
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_key
```

### Docker Configuration
- **Port**: 3000
- **Base Image**: Node.js 18 Alpine
- **Web Server**: Nginx
- **Build Type**: Multi-stage production build

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

## 🤝 Contributing

This is a production-ready application. For modifications:

1. Test thoroughly with various search queries
2. Maintain the multi-strategy search approach
3. Ensure responsive design across devices
4. Verify Docker builds successfully

## 📄 License

This project is configured for public use with read-only database access.

## 🔗 Database

Connected to a pre-configured Supabase instance with:
- **Read-only access**: Safe for public deployment
- **Row Level Security**: Data protection enabled
- **Public credentials**: Safe to share (anon key only)

---

**Version 2.0** - Enhanced with advanced search capabilities and comprehensive zone information display.
