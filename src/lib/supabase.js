import { createClient } from '@supabase/supabase-js'

// Supabase configuration
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:8000'
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'your-anon-key-here'

export const supabase = createClient(supabaseUrl, supabaseKey)

// Search zones function that calls the RPC
export async function searchZones(query) {
  try {
    const { data, error } = await supabase.rpc('search_zones', {
      search_query: query
    })
    
    if (error) {
      console.error('Error searching zones:', error)
      throw error
    }
    
    return data
  } catch (error) {
    console.error('Search zones error:', error)
    throw error
  }
}