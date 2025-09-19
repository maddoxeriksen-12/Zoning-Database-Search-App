# 🚀 Quick Start Guide

This app is **pre-configured** and ready to use with the zoning database!

## Installation & Running

```bash
# 1. Clone the repository
git clone [your-repo-url]
cd zoning-search-app

# 2. Install dependencies
npm install

# If you get permission errors, run:
# sudo chown -R $(whoami) ~/.npm
# Then try npm install again

# 3. Start the app
npm run dev
```

The app will open at `http://localhost:5173`

## That's it! 🎉

The app is already configured with:
- ✅ Supabase connection
- ✅ Read-only access to zoning data
- ✅ Search functionality ready to use

## Troubleshooting

### NPM Permission Errors
If you see "EACCES: permission denied" errors:
```bash
sudo chown -R $(whoami) ~/.npm
npm cache clean --force
npm install
```

### Test the Connection
To verify the Supabase connection works:
```bash
npm run test-connection
```

## How to Search

- Type a zone code like "R-20"
- Add a municipality like "R-20 Brick"
- Include state like "B-1 Middletown NJ"
- Click Search or press Enter

## Security

This app has **read-only** access. It cannot:
- ❌ Modify any data
- ❌ Delete any records
- ❌ Add new zones

It can only:
- ✅ Search zones
- ✅ View results

Your database is safe!