// Firebase Configuration for InfinityAI.Pro
import { initializeApp, getApps } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged, User } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc, updateDoc, collection, query, where, getDocs } from 'firebase/firestore';

// Firebase configuration (loaded from environment variables - no hardcoded keys)
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "",
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || ""
};

// Debug: Log config version (Check this in browser console)
if (typeof window !== 'undefined') {
  console.log('[InfinityAI] Firebase Init v20251222-02 - Checking Keys:', {
    hasApiKey: !!firebaseConfig.apiKey,
    projectId: firebaseConfig.projectId
  });
}

// Initialize Firebase only in the browser (avoid running during Next.js prerender/SSR)
let app = undefined as ReturnType<typeof initializeApp> | undefined;
let authClient = null as ReturnType<typeof getAuth> | null;
let dbClient = null as ReturnType<typeof getFirestore> | null;

if (typeof window !== 'undefined') {
  // Only initialize in browser contexts
  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
  authClient = getAuth(app);
  dbClient = getFirestore(app);
}

// Exports: may be null during SSR; callers must handle null (we add guards in this file)
export const auth = authClient;
export const db = dbClient;
export const googleProvider = typeof window !== 'undefined' ? new GoogleAuthProvider() : null;

// ============================================
// Authentication Functions
// ============================================

export async function signInWithGoogle() {
  if (!auth || !googleProvider) {
    console.warn('signInWithGoogle called before Firebase initialization (SSR or missing config)');
    return { success: false, error: 'Firebase not initialized' } as const;
  }

  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;

    // Create or update user profile in Firestore
    const profile = await createOrUpdateUserProfile(user);

    return { success: true, user, profile } as const;
  } catch (error) {
    console.error('Google sign-in error:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' } as const;
  }
}

export async function logOut() {
  if (!auth) {
    console.warn('logOut called before Firebase initialization (SSR or missing config); skipping signOut');
    return { success: true } as const;
  }

  try {
    await signOut(auth);
    return { success: true } as const;
  } catch (error) {
    console.error('Sign-out error:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' } as const;
  }
}

export function onAuthChange(callback: (user: User | null) => void) {
  // If auth is not initialized (SSR), call the callback with null and return a noop
  if (!auth) {
    console.warn('onAuthChange registered before Firebase initialization (SSR); invoking callback(null) and returning noop');
    // Call callback asynchronously to mirror onAuthStateChanged behavior
    setTimeout(() => callback(null), 0);
    return () => {};
  }

  return onAuthStateChanged(auth, callback);
}

// ============================================
// User Profile Functions (Firestore)
// ============================================

export interface UserProfile {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  createdAt: Date;
  lastLoginAt: Date;
  dhanConnected: boolean;
  dhanClientId?: string;
  settings: {
    riskLevel: 'conservative' | 'moderate' | 'aggressive';
    maxPositionSize: number;
    stopLossPercent: number;
    autoTrading: boolean;
    notifications: {
      email: boolean;
      push: boolean;
      tradeAlerts: boolean;
      dailyReports: boolean;
    };
  };
}

export async function createOrUpdateUserProfile(user: User): Promise<UserProfile | null> {
  if (!db) {
    // Running during SSR/prerender — skip Firebase calls
    console.warn('createOrUpdateUserProfile called during SSR; skipping Firebase operations');
    return null;
  }

  try {
    const userRef = doc(db, 'users', user.uid);
    const userSnap = await getDoc(userRef);

    if (userSnap.exists()) {
      // Update last login
      await updateDoc(userRef, {
        lastLoginAt: new Date(),
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
      });
      return userSnap.data() as UserProfile;
    } else {
      // Create new profile
      const newProfile: UserProfile = {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
        createdAt: new Date(),
        lastLoginAt: new Date(),
        dhanConnected: false,
        settings: {
          riskLevel: 'moderate',
          maxPositionSize: 25000,
          stopLossPercent: 2,
          autoTrading: false,
          notifications: {
            email: true,
            push: true,
            tradeAlerts: true,
            dailyReports: false,
          },
        },
      };

      await setDoc(userRef, newProfile);
      return newProfile;
    }
  } catch (error) {
    console.error('Error creating/updating user profile:', error);
    return null;
  }
}

export async function getUserProfile(uid: string): Promise<UserProfile | null> {
  if (!db) {
    console.warn('getUserProfile called during SSR; returning null');
    return null;
  }

  try {
    const userRef = doc(db, 'users', uid);
    const userSnap = await getDoc(userRef);

    if (userSnap.exists()) {
      return userSnap.data() as UserProfile;
    }
    return null;
  } catch (error) {
    console.error('Error getting user profile:', error);
    return null;
  }
}

export async function updateUserSettings(uid: string, settings: Partial<UserProfile['settings']>): Promise<boolean> {
  if (!db) {
    console.warn('updateUserSettings called during SSR; skipping');
    return false;
  }

  try {
    const userRef = doc(db, 'users', uid);
    await updateDoc(userRef, {
      'settings': settings,
    });
    return true;
  } catch (error) {
    console.error('Error updating user settings:', error);
    return false;
  }
}

export async function updateDhanConnection(uid: string, connected: boolean, clientId?: string): Promise<boolean> {
  if (!db) {
    console.warn('updateDhanConnection called during SSR; skipping');
    return false;
  }

  try {
    const userRef = doc(db, 'users', uid);
    await updateDoc(userRef, {
      dhanConnected: connected,
      dhanClientId: clientId || null,
    });
    return true;
  } catch (error) {
    console.error('Error updating Dhan connection:', error);
    return false;
  }
}

// ============================================
// Trade History Functions (Firestore)
// ============================================

export interface TradeRecord {
  id: string;
  userId: string;
  symbol: string;
  securityId: string;
  transactionType: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  productType: string;
  orderType: string;
  status: 'EXECUTED' | 'PENDING' | 'CANCELLED' | 'REJECTED';
  orderId?: string;
  pnl?: number;
  createdAt: Date;
  executedAt?: Date;
  aiConfidence?: number;
  aiSignal?: 'BUY' | 'SELL' | 'HOLD';
}

export async function saveTradeRecord(trade: Omit<TradeRecord, 'id'>): Promise<string | null> {
  if (!db) {
    console.warn('saveTradeRecord called during SSR; skipping');
    return null;
  }

  try {
    const tradesRef = collection(db, 'trades');
    const newTradeRef = doc(tradesRef);

    await setDoc(newTradeRef, {
      ...trade,
      id: newTradeRef.id,
    });

    return newTradeRef.id;
  } catch (error) {
    console.error('Error saving trade record:', error);
    return null;
  }
}

export async function getUserTrades(userId: string, limit = 50): Promise<TradeRecord[]> {
  if (!db) {
    console.warn('getUserTrades called during SSR; returning empty list');
    return [];
  }

  try {
    const tradesRef = collection(db, 'trades');
    const q = query(tradesRef, where('userId', '==', userId));
    const querySnapshot = await getDocs(q);

    const trades: TradeRecord[] = [];
    querySnapshot.forEach((doc) => {
      trades.push(doc.data() as TradeRecord);
    });

    // Sort by createdAt descending and limit
    return trades
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      .slice(0, limit);
  } catch (error) {
    console.error('Error getting user trades:', error);
    return [];
  }
}

// ============================================
// AI Signals History (Firestore)
// ============================================

export interface SignalRecord {
  id: string;
  userId: string;
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  analysis: {
    technical_score: number;
    sentiment_score: number;
    ml_prediction: number;
  };
  actedOn: boolean;
  tradeId?: string;
  createdAt: Date;
}

export async function saveSignalRecord(signal: Omit<SignalRecord, 'id'>): Promise<string | null> {
  if (!db) {
    console.warn('saveSignalRecord called during SSR; skipping');
    return null;
  }

  try {
    const signalsRef = collection(db, 'signals');
    const newSignalRef = doc(signalsRef);

    await setDoc(newSignalRef, {
      ...signal,
      id: newSignalRef.id,
    });

    return newSignalRef.id;
  } catch (error) {
    console.error('Error saving signal record:', error);
    return null;
  }
}

export async function getUserSignals(userId: string, limit = 100): Promise<SignalRecord[]> {
  if (!db) {
    console.warn('getUserSignals called during SSR; returning empty list');
    return [];
  }

  try {
    const signalsRef = collection(db, 'signals');
    const q = query(signalsRef, where('userId', '==', userId));
    const querySnapshot = await getDocs(q);

    const signals: SignalRecord[] = [];
    querySnapshot.forEach((doc) => {
      signals.push(doc.data() as SignalRecord);
    });

    return signals
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      .slice(0, limit);
  } catch (error) {
    console.error('Error getting user signals:', error);
    return [];
  }
}

export default app;
