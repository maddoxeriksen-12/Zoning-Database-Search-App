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
  const municipalityParts = []
  
  // Common state abbreviations
  const states = ['NJ', 'NY', 'PA', 'CT', 'DE', 'MD', 'CA', 'FL', 'TX', 'MA']
  
  // Zone code patterns (R-20, B-1, M-1, etc.)
  // Must be 1-2 letters followed by optional dash and numbers/letters
  const zonePattern = /^[A-Z]{1,2}-[A-Z0-9]+$|^[A-Z]{1,2}[0-9]+$/i
  
  // County patterns (ends with "County")
  const countyPattern = /county$/i
  
  // First pass: identify zones, states, and counties
  const usedIndices = new Set()
  
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i]
    const upperPart = part.toUpperCase()
    
    // Check for state
    if (states.includes(upperPart)) {
      result.state = upperPart
      usedIndices.add(i)
      continue
    }
    
    // Check for zone code
    if (zonePattern.test(part)) {
      result.zone = part.toUpperCase()
      usedIndices.add(i)
      continue
    }
    
    // Check for county (look for "County" or multi-word county names)
    if (countyPattern.test(part) && i > 0) {
      const prevWord = parts[i-1]
      result.county = `${prevWord} ${part}`
      usedIndices.add(i)
      usedIndices.add(i-1)
      continue
    } else if (countyPattern.test(part)) {
      result.county = part
      usedIndices.add(i)
      continue
    }
  }
  
  // Second pass: everything else becomes municipality
  for (let i = 0; i < parts.length; i++) {
    if (!usedIndices.has(i)) {
      municipalityParts.push(parts[i])
    }
  }
  
  if (municipalityParts.length > 0) {
    result.municipality = municipalityParts.join(' ')
  }
  
  return result
}

/**
 * Check if parsed query needs disambiguation
 */
export function needsDisambiguation(parsed, searchResults = []) {
  const missing = []
  
  // Don't require disambiguation if we're doing a valid town-only search and got good results
  if (parsed.municipality && !parsed.zone && searchResults.length > 0 && searchResults.length <= 10) {
    return missing // No disambiguation needed for town searches with reasonable results
  }
  
  // Always need state for proper search (unless doing town-only search)
  if (!parsed.state && !parsed.municipality) {
    missing.push('state')
  }
  
  // Need either county, municipality, or zone
  if (!parsed.county && !parsed.municipality && !parsed.zone) {
    missing.push('location (county, municipality, or zone code)')
  }
  
  // If we have too many results, might need disambiguation
  if (searchResults.length > 15) {
    missing.push('more specific location or zone code')
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