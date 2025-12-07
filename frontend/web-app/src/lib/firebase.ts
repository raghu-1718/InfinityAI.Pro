// Firebase Configuration for InfinityAI.Pro
import { initializeApp, getApps } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged, User } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc, updateDoc, collection, query, where, getDocs } from 'firebase/firestore';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAnEUI1GqUnAL8h3GFQMmnpBXv7nh6tu3k",
  authDomain: "gen-lang-client-0779271931.firebaseapp.com",
  projectId: "gen-lang-client-0779271931",
  storageBucket: "gen-lang-client-0779271931.firebasestorage.app",
  messagingSenderId: "429140669077",
  appId: "1:429140669077:web:e071ad7a136c74a3ea219c"
};

// Initialize Firebase (prevent multiple initializations)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

// Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();

// ============================================
// Authentication Functions
// ============================================

export async function signInWithGoogle() {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;

    // Create or update user profile in Firestore
    await createOrUpdateUserProfile(user);

    return { success: true, user };
  } catch (error) {
    console.error('Google sign-in error:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function logOut() {
  try {
    await signOut(auth);
    return { success: true };
  } catch (error) {
    console.error('Sign-out error:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export function onAuthChange(callback: (user: User | null) => void) {
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
