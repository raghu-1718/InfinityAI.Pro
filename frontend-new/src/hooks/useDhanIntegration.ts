import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { ENDPOINTS } from '../utils/constants'

type DhanStatus = {
  status: string
  oauth_active: boolean
  oauth_configured: boolean
  client_id?: string
  redirect_uri: string
  postback_uri: string
  scopes: string[]
  connected: boolean
  account_details?: Record<string, unknown>
  endpoints: Record<string, string>
  integration_status: string
}

type CallbackUrls = {
  redirect_url: string
  postback_url: string
  engine_c_base: string
}

export function useDhanStatus() {
  return useQuery<DhanStatus>({
    queryKey: ['dhan-status'],
    queryFn: async () => {
      const url = `${ENDPOINTS.engineC.baseUrl}/api/dhan/status`
      const { data } = await axios.get(url)
      return data
    },
    refetchInterval: 60_000,
  })
}

export function useDhanCallbackUrls() {
  return useQuery<CallbackUrls>({
    queryKey: ['dhan-callback-urls'],
    queryFn: async () => {
      const url = `${ENDPOINTS.engineC.baseUrl}/api/dhan/callback-urls`
      const { data } = await axios.get(url)
      return data
    },
  })
}

export async function updateDhanAccessToken(accessToken: string, persist = true) {
  const url = `${ENDPOINTS.engineC.baseUrl}/api/dhan/token`
  const { data } = await axios.post(url, { access_token: accessToken, persist })
  return data as { status: string; persisted: boolean; timestamp: string } | { status: string; error: string }
}

export async function updateDhanCredentials(args: { client_id?: string; api_key?: string; api_secret?: string }) {
  const url = `${ENDPOINTS.engineC.baseUrl}/api/dhan/credentials`
  // Engine C expects a fixed dev API key by default. Use that to avoid 401s in dev.
  const headers = { Authorization: 'Bearer valid_api_key' }
  const { data } = await axios.post(url, args, { headers })
  return data as { status: string; persisted: Record<string, boolean> } | { status: string; error: string }
}

export async function initiateDhanOAuth() {
  const url = `${ENDPOINTS.engineC.baseUrl}/api/auth/dhan/initiate`
  const { data } = await axios.get(url)
  // data.auth_url is expected
  return data as { status: string; auth_url: string; state: string }
}
