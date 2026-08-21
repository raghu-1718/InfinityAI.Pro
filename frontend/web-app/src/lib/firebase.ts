export interface UserProfile {
  uid: string;
  email: string;
  displayName: string;
  photoURL?: string | null;
  dhanConnected: boolean;
  dhanClientId?: string;
}
