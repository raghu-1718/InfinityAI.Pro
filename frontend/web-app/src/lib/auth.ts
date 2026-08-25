import {
  GoogleAuthProvider,
  type User as FirebaseUser,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
} from "firebase/auth";
import { firebaseAuth, isFirebaseConfigured, type UserProfile } from "@/lib/firebase";

export interface User {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
}

const LOCAL_USER_KEY = "infinityai_local_auth_user";

function normalizeUser(user: FirebaseUser | null): User | null {
  if (!user) return null;

  return {
    uid: user.uid,
    email: user.email,
    displayName: user.displayName,
    photoURL: user.photoURL,
  };
}

function getLocalUser(): User | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(LOCAL_USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

function setLocalUser(user: User | null): void {
  if (typeof window === "undefined") return;
  if (!user) {
    localStorage.removeItem(LOCAL_USER_KEY);
    return;
  }
  localStorage.setItem(LOCAL_USER_KEY, JSON.stringify(user));
}

export function onAuthChange(callback: (user: User | null) => void): () => void {
  if (!firebaseAuth || !isFirebaseConfigured) {
    callback(getLocalUser());
    return () => {};
  }

  return onAuthStateChanged(firebaseAuth, (user) => {
    const normalized = normalizeUser(user);
    if (normalized) {
      setLocalUser(normalized);
    } else {
      setLocalUser(null);
    }
    callback(normalized);
  });
}

export async function signInWithGoogle(): Promise<{
  success: boolean;
  user?: User;
  profile?: UserProfile;
  error?: string;
}> {
  if (!firebaseAuth || !isFirebaseConfigured) {
    return {
      success: false,
      error:
        "Firebase Authentication is not configured. Add the NEXT_PUBLIC_FIREBASE_* values and enable Google sign-in in Firebase.",
    };
  }

  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });

  const result = await signInWithPopup(firebaseAuth, provider);
  const user = normalizeUser(result.user);

  if (!user) {
    return { success: false, error: "Google sign-in completed without a user payload." };
  }

  setLocalUser(user);

  const profile: UserProfile = {
    uid: user.uid,
    email: user.email ?? "",
    displayName: user.displayName ?? "InfinityAI User",
    photoURL: user.photoURL ?? null,
    dhanConnected: true,
    dhanClientId: "owner-user",
  };

  return { success: true, user, profile };
}

export async function logOut(): Promise<{ success: boolean; error?: string }> {
  if (firebaseAuth) {
    await signOut(firebaseAuth);
  }
  setLocalUser(null);
  return { success: true };
}

export async function getUserProfile(uid: string): Promise<UserProfile> {
  const localUser = getLocalUser();

  if (firebaseAuth?.currentUser) {
    const user = normalizeUser(firebaseAuth.currentUser);
    return {
      uid: user?.uid ?? uid,
      email: user?.email ?? localUser?.email ?? "",
      displayName: user?.displayName ?? localUser?.displayName ?? "InfinityAI User",
      photoURL: user?.photoURL ?? localUser?.photoURL ?? null,
      dhanConnected: true,
      dhanClientId: "owner-user",
    };
  }

  return {
    uid: localUser?.uid ?? uid,
    email: localUser?.email ?? "",
    displayName: localUser?.displayName ?? "InfinityAI User",
    photoURL: localUser?.photoURL ?? null,
    dhanConnected: true,
    dhanClientId: "owner-user",
  };
}
