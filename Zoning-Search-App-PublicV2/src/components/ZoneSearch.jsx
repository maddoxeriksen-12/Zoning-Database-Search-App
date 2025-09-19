import { useState, useEffect } from 'react'
import { searchZones } from '../lib/supabase'
import { 
  parseSearchInput, 
  needsDisambiguation, 
  generateSearchSuggestions, 
  buildSearchQuery 
} from '../utils/searchParser'

// Filter results to show the most relevant zones
function filterMostRelevantZones(results, parsed) {
  if (!results || results.length === 0) return []
  
  // Score each result based on relevance
  const scoredResults = results.map(zone => {
    let score = 0
    
    // Exact zone code match gets highest priority
    if (parsed.zone && zone.zone_code === parsed.zone) {
      score += 100
    }
    
    // Partial zone code match (R-22 matches R-22A, R-22B, R-15 Nonconforming, etc.)
    // Check if the zone code starts with the search term followed by space or dash or letter
    if (parsed.zone && zone.zone_code?.startsWith(parsed.zone)) {
      const remainder = zone.zone_code.slice(parsed.zone.length)
      // If remainder is empty (exact match) or starts with space, dash, or letter
      if (remainder === '' || /^[\s\-A-Z]/.test(remainder)) {
        score += 80
      }
    }
    
    // Also check if the zone code contains the search term (for complex cases)
    if (parsed.zone && zone.zone_code?.includes(parsed.zone) && !zone.zone_code?.startsWith(parsed.zone)) {
      score += 60
    }
    
    // Exact municipality match gets high priority
    if (parsed.municipality && zone.municipality?.toLowerCase() === parsed.municipality.toLowerCase()) {
      score += 50
    }
    
    // Partial municipality match gets medium priority
    if (parsed.municipality && zone.municipality?.toLowerCase().includes(parsed.municipality.toLowerCase())) {
      score += 25
    }
    
    // State match gets some priority
    if (parsed.state && zone.state === parsed.state) {
      score += 10
    }
    
    // County match gets some priority
    if (parsed.county && zone.county?.toLowerCase().includes(parsed.county.toLowerCase())) {
      score += 15
    }
    
    return { ...zone, relevanceScore: score }
  })
  
  // Sort by relevance score (highest first)
  const sortedResults = scoredResults.sort((a, b) => b.relevanceScore - a.relevanceScore)
  
  // Determine how many results to return based on search type
  let maxResults = 2 // Default limit
  
  // If searching by municipality only (like "Brick"), show more results
  if (parsed.municipality && !parsed.zone && !parsed.county) {
    maxResults = 10 // Show up to 10 zones for town-only searches
  }
  
  // If searching by partial zone code (R-22 finding R-22A, R-22B), show related zones
  if (parsed.zone && sortedResults.some(r => r.zone_code?.startsWith(parsed.zone) && r.zone_code !== parsed.zone)) {
    maxResults = 5 // Show up to 5 related zone codes
  }
  
  return sortedResults
    .slice(0, maxResults)
    .map(({ relevanceScore, ...zone }) => zone) // Remove the score from final result
}

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
      
      // Try multiple search strategies to find partial matches
      let results = await searchZones(searchQuery)
      let allFoundResults = [...(results || [])]
      
      // If we're looking for a specific zone in a specific municipality, try multiple search strategies
      if (parsed.zone && parsed.municipality) {
        
        // Strategy 1: Search by municipality + state only
        const municipalityQuery = parsed.state ? `${parsed.municipality} ${parsed.state}` : parsed.municipality
        const municipalityResults = await searchZones(municipalityQuery)
        
        if (municipalityResults && municipalityResults.length > 0) {
          // Filter for zones that START with our target zone code
          const partialMatches = municipalityResults.filter(zone => {
            const zoneMatches = zone.zone_code?.startsWith(parsed.zone)
            const municipalityMatches = !parsed.municipality || zone.municipality?.toLowerCase() === parsed.municipality.toLowerCase()
            const stateMatches = !parsed.state || zone.state === parsed.state
            
            return zoneMatches && municipalityMatches && stateMatches
          })
          
          // Add to results
          partialMatches.forEach(zone => {
            if (!allFoundResults.find(existing => 
              existing.zone_code === zone.zone_code && 
              existing.municipality === zone.municipality &&
              existing.state === zone.state
            )) {
              allFoundResults.push(zone)
            }
          })
        }
        
        // Strategy 2: Search by just zone code if we still don't have enough results
        if (allFoundResults.length < 3) {
          const zoneResults = await searchZones(parsed.zone)
          
          if (zoneResults && zoneResults.length > 0) {
            // Filter for zones in our target municipality/state
            const zoneMatches = zoneResults.filter(zone => {
              const municipalityMatches = !parsed.municipality || zone.municipality?.toLowerCase() === parsed.municipality.toLowerCase()
              const stateMatches = !parsed.state || zone.state === parsed.state
              
              return municipalityMatches && stateMatches
            })
            
            // Add to results
            zoneMatches.forEach(zone => {
              if (!allFoundResults.find(existing => 
                existing.zone_code === zone.zone_code && 
                existing.municipality === zone.municipality &&
                existing.state === zone.state
              )) {
                allFoundResults.push(zone)
              }
            })
          }
        }
        
        // Strategy 3: Try searching for "Nonconforming" if it's an R zone
        if (parsed.zone.startsWith('R-') && allFoundResults.length < 3) {
          const nonconformingQuery = parsed.state ? 
            `Nonconforming ${parsed.municipality} ${parsed.state}` : 
            `Nonconforming ${parsed.municipality}`
          const nonconformingResults = await searchZones(nonconformingQuery)
          
          if (nonconformingResults && nonconformingResults.length > 0) {
            // Filter for zones that contain our target zone code
            const nonconformingMatches = nonconformingResults.filter(zone => {
              const zoneMatches = zone.zone_code?.includes(parsed.zone)
              const municipalityMatches = !parsed.municipality || zone.municipality?.toLowerCase() === parsed.municipality.toLowerCase()
              const stateMatches = !parsed.state || zone.state === parsed.state
              
              return zoneMatches && municipalityMatches && stateMatches
            })
            
            // Add to results
            nonconformingMatches.forEach(zone => {
              if (!allFoundResults.find(existing => 
                existing.zone_code === zone.zone_code && 
                existing.municipality === zone.municipality &&
                existing.state === zone.state
              )) {
                allFoundResults.push(zone)
              }
            })
          }
        }
      }
      
      results = allFoundResults
      
      // Filter and limit results to 1-2 most relevant zones
      const filteredResults = filterMostRelevantZones(results || [], parsed)
      setSearchResults(filteredResults)

      // Check if we need disambiguation based on filtered results
      const missing = needsDisambiguation(parsed, filteredResults)
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

      {/* Display key zoning standards */}
      <div className="zone-standards">
        <h4>📋 Zone Requirements:</h4>
        <div className="standards-grid">
          {zone.area_sqft_interior_lots ? (
            <div className="standard">
              <span className="label">Minimum Area:</span>
              <span className="value">{zone.area_sqft_interior_lots.toLocaleString()} sq ft</span>
            </div>
          ) : (
            <div className="standard">
              <span className="label">Minimum Area:</span>
              <span className="value">Not specified</span>
            </div>
          )}
          
          {zone.frontage_interior_lots ? (
            <div className="standard">
              <span className="label">Minimum Frontage:</span>
              <span className="value">{zone.frontage_interior_lots} ft</span>
            </div>
          ) : (
            <div className="standard">
              <span className="label">Minimum Frontage:</span>
              <span className="value">Not specified</span>
            </div>
          )}
          
          {zone.max_building_coverage_percent ? (
            <div className="standard">
              <span className="label">Buildable Lot Area:</span>
              <span className="value">Up to {zone.max_building_coverage_percent}% coverage</span>
            </div>
          ) : (
            <div className="standard">
              <span className="label">Buildable Lot Area:</span>
              <span className="value">Not specified</span>
            </div>
          )}
          
          {zone.depth_interior_lots_ft && (
            <div className="standard">
              <span className="label">Minimum Depth:</span>
              <span className="value">{zone.depth_interior_lots_ft} ft</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}