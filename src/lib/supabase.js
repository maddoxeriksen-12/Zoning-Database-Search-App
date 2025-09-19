import { createClient } from '@supabase/supabase-js'

// Public Supabase configuration
// IMPORTANT: These are PUBLIC credentials that are safe to expose
// The anon key only allows read access through RLS policies
// Your database is protected by Row Level Security (RLS)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://twlndyixqxfqpdywdlyv.supabase.co'
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR3bG5keWl4cXhmcXBkeXdkbHl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgxMTk1NjQsImV4cCI6MjA3MzY5NTU2NH0._AW0A-E2zArk5UFyA_S0N5CqFgtDdntMDLb8ZSes73I'

// These credentials are PUBLIC and safe to share
// The anon key is designed to be public - your data is protected by Row Level Security

export const supabase = createClient(supabaseUrl, supabaseKey)

// Search zones function that calls the RPC
// This is a read-only function that cannot modify data
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