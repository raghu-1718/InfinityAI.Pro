/**
 * User Identity Management
 * Provides consistent user identification across the application
 *
 * Priority order for user ID:
 * 1. Dhan Client ID (when connected - most stable identifier)
 * 2. Firebase UID (when authenticated via Firebase)
 * 3. Session-based ID (for coupon auth)
 * 4. Generated fallback ID (temporary until proper auth)
 */

// Storage keys
const DHAN_CLIENT_ID_KEY = 'dhan_client_id';
const USER_ID_KEY = 'infinityai_user_id';
const AUTH_TYPE_KEY = 'infinityai_auth_type';
const COUPON_SESSION_KEY = 'infinityai_coupon_session';

/**
 * Get the current user's ID
 * Uses the most reliable identifier available
 */
export function getUserId(): string {
  if (typeof window === 'undefined') return 'default_user';

  // Priority 1: Dhan Client ID (10-digit number) - most stable for trading
  const dhanClientId = localStorage.getItem(DHAN_CLIENT_ID_KEY);
  if (dhanClientId && /^\d{10}$/.test(dhanClientId)) {
    return dhanClientId;
  }

  // Priority 2: Check auth type and get appropriate ID
  const authType = localStorage.getItem(AUTH_TYPE_KEY);

  if (authType === 'coupon') {
    // Get coupon session user ID
    const couponSession = localStorage.getItem(COUPON_SESSION_KEY);
    if (couponSession) {
      try {
        const session = JSON.parse(couponSession);
        if (session.userId) {
          return session.userId;
        }
      } catch {
        console.warn('Failed to parse coupon session');
      }
    }
  }

  // Priority 3: Generated fallback ID (for unauthenticated users)
  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    localStorage.setItem(USER_ID_KEY, userId);
  }
  return userId;
}

/**
 * Store the Dhan Client ID for future sessions
 * This becomes the primary identifier once connected
 */
export function setDhanClientId(clientId: string): void {
  if (typeof window !== 'undefined' && clientId && /^\d{10}$/.test(clientId)) {
    localStorage.setItem(DHAN_CLIENT_ID_KEY, clientId);
    console.log('✅ Dhan Client ID stored:', clientId);
  }
}

/**
 * Get the stored Dhan Client ID
 */
export function getDhanClientId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(DHAN_CLIENT_ID_KEY);
}

/**
 * Clear the Dhan Client ID (on disconnect)
 */
export function clearDhanClientId(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(DHAN_CLIENT_ID_KEY);
  }
}

/**
 * Check if user has a Dhan account connected
 */
export function isDhanConnected(): boolean {
  const clientId = getDhanClientId();
  return !!clientId && /^\d{10}$/.test(clientId);
}

/**
 * Get user display info
 */
export function getUserDisplayInfo(): {
  userId: string;
  isDhanConnected: boolean;
  displayName: string;
} {
  const userId = getUserId();
  const dhanConnected = isDhanConnected();

  let displayName = 'Guest User';
  if (dhanConnected) {
    displayName = `Dhan User ${userId}`;
  } else if (userId.startsWith('user_')) {
    displayName = 'Guest';
  }

  return {
    userId,
    isDhanConnected: dhanConnected,
    displayName
  };
}

/**
 * Clear all user identification data (for logout)
 */
export function clearUserIdentity(): void {
  if (typeof window === 'undefined') return;
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
  clearUserIdentity
};

export default userUtils;
