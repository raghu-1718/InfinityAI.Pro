// Firebase Service Logic - Unified with config.ts
import { auth, db, functions } from "./firebase/config";
import {
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  User,
} from "firebase/auth";
import {
  doc,
  setDoc,
  getDoc,
  updateDoc,
  collection,
  query,
  where,
  getDocs,
} from "firebase/firestore";

// Re-export instances for compatibility
export { auth, db, functions };
export const googleProvider = new GoogleAuthProvider();

// ============================================
// Authentication Functions
// ============================================

export async function signInWithGoogle() {
  if (!auth) return { success: false, error: "Firebase not initialized" };

  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;
    const profile = await createOrUpdateUserProfile(user);
    return { success: true, user, profile };
  } catch (error: any) {
    console.error("Google sign-in error:", error);
    return { success: false, error: error.message };
  }
}

export async function logOut() {
  if (!auth) return { success: true };
  try {
    await signOut(auth);
    return { success: true };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}

export function onAuthChange(callback: (user: User | null) => void) {
  if (!auth) {
    setTimeout(() => callback(null), 0);
    return () => {};
  }
  return onAuthStateChanged(auth, callback);
}

// ============================================
// User Profile Functions
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
    riskLevel: "conservative" | "moderate" | "aggressive";
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

export async function createOrUpdateUserProfile(
  user: User
): Promise<UserProfile | null> {
  if (!db) return null;

  try {
    const userRef = doc(db, "users", user.uid);
    const userSnap = await getDoc(userRef);

    if (userSnap.exists()) {
      await updateDoc(userRef, {
        lastLoginAt: new Date(),
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
      });
      return userSnap.data() as UserProfile;
    } else {
      const newProfile: UserProfile = {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
        createdAt: new Date(),
        lastLoginAt: new Date(),
        dhanConnected: false,
        settings: {
          riskLevel: "moderate",
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
    console.error("Error creating user profile:", error);
    return null;
  }
}

export async function getUserProfile(uid: string): Promise<UserProfile | null> {
  if (!db) return null;
  try {
    const userSnap = await getDoc(doc(db, "users", uid));
    return userSnap.exists() ? (userSnap.data() as UserProfile) : null;
  } catch (error) {
    return null;
  }
}

export async function updateUserSettings(
  uid: string,
  settings: Partial<UserProfile["settings"]>
): Promise<boolean> {
  if (!db) return false;
  try {
    await updateDoc(doc(db, "users", uid), { settings: settings });
    return true;
  } catch {
    return false;
  }
}

export async function updateDhanConnection(
  uid: string,
  connected: boolean,
  clientId?: string
): Promise<boolean> {
  if (!db) return false;
  try {
    await updateDoc(doc(db, "users", uid), {
      dhanConnected: connected,
      dhanClientId: clientId || null,
    });
    return true;
  } catch {
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
  transactionType: "BUY" | "SELL";
  quantity: number;
  price: number;
  productType: string;
  orderType: string;
  status: "EXECUTED" | "PENDING" | "CANCELLED" | "REJECTED";
  orderId?: string;
  pnl?: number;
  createdAt: Date;
  executedAt?: Date;
  aiConfidence?: number;
  aiSignal?: "BUY" | "SELL" | "HOLD";
}

export async function saveTradeRecord(
  trade: Omit<TradeRecord, "id">
): Promise<string | null> {
  if (!db) return null;

  try {
    const tradesRef = collection(db, "trades");
    const newTradeRef = doc(tradesRef);

    await setDoc(newTradeRef, {
      ...trade,
      id: newTradeRef.id,
    });

    return newTradeRef.id;
  } catch (error) {
    console.error("Error saving trade record:", error);
    return null;
  }
}

export async function getUserTrades(
  userId: string,
  limit = 50
): Promise<TradeRecord[]> {
  if (!db) return [];

  try {
    const tradesRef = collection(db, "trades");
    const q = query(tradesRef, where("userId", "==", userId));
    const querySnapshot = await getDocs(q);

    const trades: TradeRecord[] = [];
    querySnapshot.forEach((doc) => {
      trades.push(doc.data() as TradeRecord);
    });

    return trades
      .sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      )
      .slice(0, limit);
  } catch (error) {
    console.error("Error getting user trades:", error);
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
  signal: "BUY" | "SELL" | "HOLD";
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

export async function saveSignalRecord(
  signal: Omit<SignalRecord, "id">
): Promise<string | null> {
  if (!db) return null;

  try {
    const signalsRef = collection(db, "signals");
    const newSignalRef = doc(signalsRef);

    await setDoc(newSignalRef, {
      ...signal,
      id: newSignalRef.id,
    });

    return newSignalRef.id;
  } catch (error) {
    console.error("Error saving signal record:", error);
    return null;
  }
}

export async function getUserSignals(
  userId: string,
  limit = 100
): Promise<SignalRecord[]> {
  if (!db) return [];

  try {
    const signalsRef = collection(db, "signals");
    const q = query(signalsRef, where("userId", "==", userId));
    const querySnapshot = await getDocs(q);

    const signals: SignalRecord[] = [];
    querySnapshot.forEach((doc) => {
      signals.push(doc.data() as SignalRecord);
    });

    return signals
      .sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      )
      .slice(0, limit);
  } catch (error) {
    console.error("Error getting user signals:", error);
    return [];
  }
}
