import { createClient } from '@supabase/supabase-js'

const rawUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL || ''
const rawKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY || ''

/**
 * Validates whether a genuine live Supabase endpoint has been configured
 */
export const isSupabaseConfigured = (): boolean => {
  return Boolean(
    rawUrl &&
    !rawUrl.includes('dummyurl') &&
    !rawUrl.includes('placeholder') &&
    !rawUrl.includes('YOUR_ACTUAL_PROJECT_ID') &&
    rawUrl.startsWith('https://')
  )
}

const supabaseUrl = isSupabaseConfigured() ? rawUrl : 'https://placeholder-disabled.supabase.co'
const supabaseAnonKey = isSupabaseConfigured() ? rawKey : 'disabled-anon-key'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// User Profile Functions
export interface UserProfile {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  createdAt: Date;
  lastLoginAt: Date;
  dhanConnected: boolean;
  dhanClientId?: string;
  settings: any;
}

export async function createOrUpdateUserProfile(user: any): Promise<UserProfile | null> {
  if (!isSupabaseConfigured()) return null;
  try {
    const { data, error } = await supabase
      .from('users')
      .upsert({
        uid: user.id,
        email: user.email,
        displayName: user.user_metadata?.full_name,
        photoURL: user.user_metadata?.avatar_url,
        lastLoginAt: new Date().toISOString(),
      })
      .select()
      .single()
    
    if (error) throw error
    return data as UserProfile
  } catch (err) {
    console.error("Error creating user profile:", err)
    return null
  }
}

export async function getUserProfile(uid: string): Promise<UserProfile | null> {
  if (!isSupabaseConfigured()) return null;
  try {
    const { data, error } = await supabase.from('users').select('*').eq('uid', uid).single()
    return error ? null : data
  } catch {
    return null
  }
}

export async function updateUserSettings(uid: string, settings: any): Promise<boolean> {
  if (!isSupabaseConfigured()) return true;
  try {
    const { error } = await supabase.from('users').update({ settings }).eq('uid', uid)
    return !error
  } catch {
    return false
  }
}

export async function updateDhanConnection(uid: string, connected: boolean, clientId?: string): Promise<boolean> {
  if (!isSupabaseConfigured()) return true;
  try {
    const { error } = await supabase.from('users').update({
      dhanConnected: connected,
      dhanClientId: clientId || null,
    }).eq('uid', uid)
    return !error
  } catch {
    return false
  }
}

// Trade History Functions
export async function saveTradeRecord(trade: any): Promise<string | null> {
  if (!isSupabaseConfigured()) return null;
  try {
    const { data, error } = await supabase.from('trades').insert([trade]).select().single()
    return error ? null : data.id
  } catch {
    return null
  }
}

export async function getUserTrades(userId: string, limit = 50): Promise<any[]> {
  if (!isSupabaseConfigured()) return [];
  try {
    const { data, error } = await supabase.from('trades')
      .select('*')
      .eq('userId', userId)
      .order('createdAt', { ascending: false })
      .limit(limit)
    return error ? [] : data
  } catch {
    return []
  }
}

// AI Signals History
export async function saveSignalRecord(signal: any): Promise<string | null> {
  if (!isSupabaseConfigured()) return null;
  try {
    const { data, error } = await supabase.from('signals').insert([signal]).select().single()
    return error ? null : data.id
  } catch {
    return null
  }
}

export async function getUserSignals(userId: string, limit = 100): Promise<any[]> {
  if (!isSupabaseConfigured()) return [];
  try {
    const { data, error } = await supabase.from('signals')
      .select('*')
      .eq('userId', userId)
      .order('createdAt', { ascending: false })
      .limit(limit)
    return error ? [] : data
  } catch {
    return []
  }
}
