// Search input parsing utilities

/**
 * Parse search input and extract components
 * Examples:
 * - "R-20 Brick NJ" -> { zone: "R-20", municipality: "Brick", state: "NJ" }
 * - "Middletown R-15" -> { zone: "R-15", municipality: "Middletown" }
 * - "Ocean County B-1" -> { zone: "B-1", county: "Ocean County" }
 */
export function parseSearchInput(input) {
  const trimmed = input.trim()
  if (!trimmed) return {}

  const parts = trimmed.split(/\s+/)
  const result = {}
  
  // Common state abbreviations
  const states = ['NJ', 'NY', 'PA', 'CT', 'DE', 'MD', 'CA', 'FL', 'TX', 'MA']
  
  // Zone code patterns (R-20, B-1, M-1, etc.)
  const zonePattern = /^[A-Z]{1,3}-?[A-Z0-9]*$/i
  
  // County patterns (ends with "County")
  const countyPattern = /county$/i
  
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i]
    const upperPart = part.toUpperCase()
    
    // Check for state
    if (states.includes(upperPart)) {
      result.state = upperPart
      continue
    }
    
    // Check for zone code
    if (zonePattern.test(part)) {
      result.zone = part.toUpperCase()
      continue
    }
    
    // Check for county (look for "County" or multi-word county names)
    if (countyPattern.test(part)) {
      // Include previous word if exists for "Ocean County", "Monmouth County", etc.
      const prevWord = i > 0 ? parts[i-1] : ''
      result.county = prevWord ? `${prevWord} ${part}` : part
      continue
    }
    
    // Remaining words likely form municipality name
    if (!result.municipality) {
      result.municipality = part
    } else {
      result.municipality += ` ${part}`
    }
  }
  
  return result
}

/**
 * Check if parsed query needs disambiguation
 */
export function needsDisambiguation(parsed, searchResults = []) {
  const missing = []
  
  // Always need state for proper search
  if (!parsed.state) {
    missing.push('state')
  }
  
  // Need either county or municipality
  if (!parsed.county && !parsed.municipality) {
    missing.push('location (county or municipality)')
  }
  
  // If we have multiple results with different locations, might need disambiguation
  if (searchResults.length > 10) {
    missing.push('more specific location')
  }
  
  return missing
}

/**
 * Generate search suggestions based on partial input
 */
export function generateSearchSuggestions(input) {
  const suggestions = []
  
  if (!input || input.length < 2) {
    return [
      'R-20 Brick NJ',
      'B-1 Middletown NJ', 
      'M-1 Ocean County NJ',
      'VZ Township NJ'
    ]
  }
  
  const parsed = parseSearchInput(input)
  
  // Suggest completing missing parts
  if (parsed.zone && !parsed.state) {
    suggestions.push(`${parsed.zone} ${parsed.municipality || 'Municipality'} NJ`)
  }
  
  if (parsed.municipality && !parsed.zone) {
    suggestions.push(`R-20 ${parsed.municipality} NJ`)
    suggestions.push(`B-1 ${parsed.municipality} NJ`)
  }
  
  return suggestions
}

/**
 * Build search query string for the RPC call
 */
export function buildSearchQuery(parsed) {
  const parts = []
  
  if (parsed.zone) parts.push(parsed.zone)
  if (parsed.municipality) parts.push(parsed.municipality)
  if (parsed.county) parts.push(parsed.county)
  if (parsed.state) parts.push(parsed.state)
  
  return parts.join(' ')
}