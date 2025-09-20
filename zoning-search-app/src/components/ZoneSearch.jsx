import { useState, useEffect } from 'react'
import { searchZones } from '../lib/supabase'
import { 
  parseSearchInput, 
  needsDisambiguation, 
  generateSearchSuggestions, 
  buildSearchQuery 
} from '../utils/searchParser'

export default function ZoneSearch() {
  const [searchInput, setSearchInput] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [disambiguation, setDisambiguation] = useState(null)
  const [showRawJson, setShowRawJson] = useState(false)

  // Generate suggestions as user types
  useEffect(() => {
    const newSuggestions = generateSearchSuggestions(searchInput)
    setSuggestions(newSuggestions)
  }, [searchInput])

  const handleSearch = async (query = searchInput) => {
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setDisambiguation(null)

    try {
      const parsed = parseSearchInput(query)
      const searchQuery = buildSearchQuery(parsed)
      
      console.log('Parsed query:', parsed)
      console.log('Search query:', searchQuery)

      const results = await searchZones(searchQuery)
      setSearchResults(results || [])

      // Check if we need disambiguation
      const missing = needsDisambiguation(parsed, results)
      if (missing.length > 0) {
        setDisambiguation({
          missing,
          parsed,
          suggestions: generateSearchSuggestions(query)
        })
      }

    } catch (err) {
      setError(err.message || 'Search failed')
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    setSearchInput(suggestion)
    handleSearch(suggestion)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="zone-search">
      <div className="search-container">
        <h1>🏠 Zoning Code Search</h1>
        <p className="description">
          Search for zoning information by zone code, municipality, and state.
          <br />
          <em>Example: "R-20 Brick NJ" or "B-1 Middletown"</em>
        </p>

        {/* Search Input */}
        <div className="search-input-group">
          <input
            type="text"
            placeholder="Enter zone code, municipality, state..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyPress={handleKeyPress}
            className="search-input"
          />
          <button 
            onClick={() => handleSearch()}
            disabled={loading}
            className="search-button"
          >
            {loading ? '🔍 Searching...' : '🔍 Search'}
          </button>
        </div>

        {/* Search Suggestions */}
        {suggestions.length > 0 && searchInput.length < 10 && (
          <div className="suggestions">
            <p className="suggestions-label">Try searching for:</p>
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="suggestion-item"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {/* Disambiguation Helper */}
        {disambiguation && (
          <div className="disambiguation">
            <h3>🤔 Need More Information</h3>
            <p>Please specify: {disambiguation.missing.join(', ')}</p>
            <div className="disambiguation-suggestions">
              {disambiguation.suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="suggestion-item"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="error">
            <h3>❌ Error</h3>
            <p>{error}</p>
          </div>
        )}

        {/* Results Controls */}
        {searchResults.length > 0 && (
          <div className="results-controls">
            <h3>📊 Found {searchResults.length} result(s)</h3>
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className="toggle-json"
            >
              {showRawJson ? '📋 Show Cards' : '🔧 Show Raw JSON'}
            </button>
          </div>
        )}

        {/* Results Display */}
        {searchResults.length > 0 && (
          <div className="results">
            {showRawJson ? (
              <pre className="raw-json">
                {JSON.stringify(searchResults, null, 2)}
              </pre>
            ) : (
              <div className="results-grid">
                {searchResults.map((zone, index) => (
                  <ZoneCard key={index} zone={zone} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Zone Card Component
function ZoneCard({ zone }) {
  return (
    <div className="zone-card">
      <div className="zone-header">
        <h3 className="zone-code">{zone.zone_code}</h3>
        {zone.zone_name && <p className="zone-name">{zone.zone_name}</p>}
      </div>
      
      <div className="zone-location">
        <p className="municipality">📍 {zone.municipality}</p>
        {zone.county && <p className="county">{zone.county}</p>}
        <p className="state">{zone.state || 'NJ'}</p>
      </div>

      {zone.ordinance_url && (
        <div className="zone-link">
          <a href={zone.ordinance_url} target="_blank" rel="noopener noreferrer">
            📄 View Ordinance
          </a>
        </div>
      )}

      {/* Display key standards if available */}
      {zone.standards && (
        <div className="zone-standards">
          <h4>Key Standards:</h4>
          <div className="standards-grid">
            {zone.area_sqft_interior_lots && (
              <div className="standard">
                <span className="label">Min Lot Area:</span>
                <span className="value">{zone.area_sqft_interior_lots.toLocaleString()} sq ft</span>
              </div>
            )}
            {zone.frontage_interior_lots && (
              <div className="standard">
                <span className="label">Min Frontage:</span>
                <span className="value">{zone.frontage_interior_lots} ft</span>
              </div>
            )}
            {zone.depth_interior_lots_ft && (
              <div className="standard">
                <span className="label">Min Depth:</span>
                <span className="value">{zone.depth_interior_lots_ft} ft</span>
              </div>
            )}
            {zone.max_building_coverage_percent && (
              <div className="standard">
                <span className="label">Max Coverage:</span>
                <span className="value">{zone.max_building_coverage_percent}%</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}