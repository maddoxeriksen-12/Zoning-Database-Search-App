# Zoning Search App

**🎯 Pre-configured and ready to use!** No setup required.

A React-based web application for searching municipal zoning codes and regulations. This app provides read-only access to a public zoning database through Supabase.

## 🔒 Security First

This app is designed with security in mind:
- **Read-only access** - Can only search and view data, cannot modify anything
- **Public anon key** - Uses Supabase's anon key which is safe to expose
- **Row Level Security** - Your database is protected by RLS policies
- **No write operations** - The app only uses a read-only RPC function

**See [SECURITY.md](SECURITY.md) for detailed security information.**

## Features

- 🔍 **Smart Search**: Search by zone code, municipality, and/or state
- 💡 **Search Suggestions**: Helpful suggestions as you type
- 📊 **Rich Results Display**: View zoning information in organized cards
- 📄 **Ordinance Links**: Direct links to source ordinances when available
- 📏 **Key Standards Display**: View important zoning metrics like lot sizes and coverage
- 🔧 **Raw JSON View**: Toggle between card view and raw JSON data

## Quick Start (For Users)

**This app comes pre-configured and ready to use!** No setup required.

1. Clone this repository:
```bash
git clone [repository-url]
cd zoning-search-app
```

2. Install dependencies:
```bash
npm install
```

3. Start the app:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

That's it! The app is pre-configured with read-only access to the zoning database.

## Usage

1. **Basic Search**: Enter a zone code (e.g., "R-20") to find all matching zones
2. **Municipality Search**: Add a municipality name (e.g., "R-20 Brick")
3. **State Search**: Include state abbreviation (e.g., "B-1 Middletown NJ")
4. **View Results**: Results appear as cards with key information
5. **View Ordinances**: Click "View Ordinance" links to see source documents

### Search Examples

- `R-20` - Find all R-20 zones
- `R-20 Brick` - Find R-20 zones in Brick municipality
- `B-1 Middletown NJ` - Find B-1 zones in Middletown, New Jersey
- `Commercial Dover` - Find commercial zones in Dover

## Developer Setup

### Setting Up Your Own Supabase Project

1. **Configure Supabase Security** (REQUIRED):
   - Enable Row Level Security on your tables
   - Create read-only policies for anonymous users
   - See [SECURITY.md](SECURITY.md) for detailed instructions

2. **Add Your Credentials**:
   
   Edit `src/lib/supabase.js` and replace the placeholders:
   ```javascript
   const supabaseUrl = 'https://your-project-id.supabase.co'
   const supabaseKey = 'your-anon-key-here' // Use anon key, NOT service key!
   ```

   Or use environment variables:
   ```bash
   cp .env.public.example .env
   # Edit .env with your credentials
   ```

3. **Important Security Notes**:
   - ✅ Use your **anon/public** key (safe to share)
   - ❌ Never use your **service** key (keep secret)
   - ✅ Enable Row Level Security on all tables
   - ✅ The anon key is designed to be public

### Deployment

#### Deploy to Vercel/Netlify

1. Fork this repository
2. Connect to Vercel or Netlify
3. Set environment variables (if using them)
4. Deploy automatically on push

#### Deploy to GitHub Pages

1. Update `vite.config.js` with your repository name
2. Run: `npm run deploy`

## How This App Maintains Security

1. **Read-Only RPC Function**: The app only calls `search_zones` which cannot modify data
2. **Anon Key Protection**: The anon key only works with Row Level Security policies
3. **No Direct Table Access**: The app doesn't directly query tables
4. **Client-Side Only**: No backend server that could be compromised

## Tech Stack

- **React** - UI framework
- **Vite** - Build tool and dev server
- **Supabase** - Database and API (read-only access)
- **CSS** - Styling (no framework dependencies)

## Project Structure

```
zoning-search-app/
├── src/
│   ├── components/
│   │   └── ZoneSearch.jsx     # Main search component
│   ├── lib/
│   │   └── supabase.js        # Supabase client configuration
│   ├── utils/
│   │   └── searchParser.js    # Search query parsing
│   └── App.jsx                # Main app component
├── .env.public.example        # Example environment variables
├── SECURITY.md               # Security documentation
└── README.md                 # This file
```

## Troubleshooting

### "Permission denied" errors
- Ensure Row Level Security is properly configured
- Verify you're using the anon key, not the service key
- Check that the `search_zones` RPC function exists and has proper permissions

### No results showing
- Verify your Supabase URL and anon key are correct
- Check browser console for errors
- Ensure the `search_zones` RPC function is working in Supabase Dashboard

## Contributing

Contributions are welcome! Please ensure any changes maintain the read-only nature of the app.

## License

MIT License - See [LICENSE](LICENSE) file

## Support

For issues or questions, please open an issue on GitHub.

## Disclaimer

This app provides read-only access to public zoning data. Always verify zoning information with official municipal sources before making any decisions.