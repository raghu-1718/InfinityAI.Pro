import type { UserProfile } from "@/lib/firebase";

export interface User {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
}

const LOCAL_USER_KEY = "infinityai_local_auth_user";

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
  callback(getLocalUser());
  return () => {};
}

export async function signInWithGoogle(): Promise<{
  success: boolean;
  user?: User;
  profile?: UserProfile;
  error?: string;
}> {
  const user: User = {
    uid: "local-user-123",
    email: "dev@localhost",
    displayName: "Local Developer",
    photoURL: null,
  };
  const profile: UserProfile = {
    uid: user.uid,
    email: user.email ?? "",
    displayName: user.displayName ?? "Local Developer",
    dhanConnected: true,
    dhanClientId: "DEV1234",
  };
  setLocalUser(user);
  return { success: true, user, profile };
}

export async function logOut(): Promise<{ success: boolean; error?: string }> {
  setLocalUser(null);
  return { success: true };
}

export async function getUserProfile(uid: string): Promise<UserProfile> {
  const user = getLocalUser();
  return {
    uid,
    email: user?.email ?? "dev@localhost",
    displayName: user?.displayName ?? "Local Developer",
    photoURL: user?.photoURL ?? null,
    dhanConnected: true,
    dhanClientId: "DEV1234",
  };
}
