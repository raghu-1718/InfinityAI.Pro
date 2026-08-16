/**
 * User Identity Management (Single-Tenant Mode)
 * Exclusively configured for Primary Owner Raghu (Client ID: 1101302170 / raghu_primary)
 */

// Storage keys
const DHAN_CLIENT_ID_KEY = "dhan_client_id";
const USER_ID_KEY = "infinityai_user_id";
const AUTH_TYPE_KEY = "infinityai_auth_type";
const COUPON_SESSION_KEY = "infinityai_coupon_session";

export const PRIMARY_USER_ID = "raghu_primary";
export const PRIMARY_DHAN_CLIENT_ID = "1101302170";
export const PRIMARY_DISPLAY_NAME = "Raghu (1101302170)";

/**
 * Get the current user's ID
 * In Single-Tenant mode, permanently resolves to raghu_primary
 */
export function getUserId(): string {
  if (typeof window === "undefined") return PRIMARY_USER_ID;
  const stored = localStorage.getItem(USER_ID_KEY);
  if (stored && stored !== "default_user" && stored !== "guest" && !stored.startsWith("user_")) {
    return stored;
  }
  return PRIMARY_USER_ID;
}

/**
 * Store the Dhan Client ID for future sessions
 */
export function setDhanClientId(clientId: string): void {
  if (typeof window !== "undefined" && clientId) {
    localStorage.setItem(DHAN_CLIENT_ID_KEY, clientId);
  }
}

/**
 * Get the stored Dhan Client ID
 */
export function getDhanClientId(): string {
  if (typeof window === "undefined") return PRIMARY_DHAN_CLIENT_ID;
  return localStorage.getItem(DHAN_CLIENT_ID_KEY) || PRIMARY_DHAN_CLIENT_ID;
}

/**
 * Clear the Dhan Client ID (on disconnect)
 */
export function clearDhanClientId(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(DHAN_CLIENT_ID_KEY);
  }
}

/**
 * Check if user has a Dhan account connected
 * Always true in Single-Tenant mode with automated Cloud Scheduler Keep-Alive
 */
export function isDhanConnected(): boolean {
  return true;
}

/**
 * Get user display info
 */
export function getUserDisplayInfo(): {
  userId: string;
  isDhanConnected: boolean;
  displayName: string;
} {
  return {
    userId: PRIMARY_USER_ID,
    isDhanConnected: true,
    displayName: PRIMARY_DISPLAY_NAME,
  };
}

/**
 * Clear user identification data
 */
export function clearUserIdentity(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(DHAN_CLIENT_ID_KEY);
  localStorage.removeItem(USER_ID_KEY);
  localStorage.removeItem(AUTH_TYPE_KEY);
  localStorage.removeItem(COUPON_SESSION_KEY);
}

const userUtils = {
  getUserId,
  setDhanClientId,
  getDhanClientId,
  clearDhanClientId,
  isDhanConnected,
  getUserDisplayInfo,
  clearUserIdentity,
  PRIMARY_USER_ID,
  PRIMARY_DHAN_CLIENT_ID,
  PRIMARY_DISPLAY_NAME,
};

export default userUtils;
