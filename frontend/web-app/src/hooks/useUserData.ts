import { useState, useEffect, useCallback } from "react";
import {
  getCredentialsAPI,
  storeCredentialsAPI,
  fetchAccountDataAPI,
} from "@/lib/cloudFunctions";

export interface AccountData {
  status: string;
  user_id: string;
  account_summary: {
    available_balance: number;
    utilized_margin: number;
    total_holdings_value: number;
    total_holdings_pnl: number;
    total_positions_pnl: number;
    net_pnl: number;
  };
  funds: {
    dhanClientId: string;
    availabelBalance: number;
    sodLimit: number;
    collateralAmount: number;
    receiveableAmount: number;
    utilizedAmount: number;
    blockedPayoutAmount: number;
    withdrawableBalance: number;
  };
  holdings: {
    count: number;
    total_value: number;
    total_pnl: number;
    data: any;
  };
  positions: {
    count: number;
    total_pnl: number;
    data: any[];
  };
  orders: {
    count: number;
    data: any[];
  };
  trades: {
    count: number;
    data: any[];
  };
  timestamp: string;
}

export interface UserCredentials {
  dhan_client_id: string;
  dhan_access_token: string;
  updated_at?: string;
}

export function useUserData(userId: string | null) {
  const [credentials, setCredentials] = useState<UserCredentials | null>(null);
  const [accountData, setAccountData] = useState<AccountData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch credentials from Cloud Function
  const fetchCredentials = useCallback(async () => {
    if (!userId) {
      setCredentials(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await getCredentialsAPI(userId);

      if (data.success) {
        setCredentials({
          dhan_client_id: data.dhan_client_id,
          dhan_access_token: data.dhan_access_token,
          updated_at: data.updated_at,
        });
      } else {
        setError(data.message || "Failed to fetch credentials");
        setCredentials(null);
      }
    } catch (err: any) {
      setError(err.message || "Network error");
      setCredentials(null);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // Store credentials in Cloud Function
  const storeCredentialsMethod = useCallback(
    async (dhanClientId: string, dhanAccessToken: string) => {
      if (!userId) {
        throw new Error("User ID is required");
      }

      setLoading(true);
      setError(null);

      try {
        const data = await storeCredentialsAPI(
          userId,
          dhanClientId,
          dhanAccessToken
        );

        if (data.success) {
          setCredentials({
            dhan_client_id: dhanClientId,
            dhan_access_token: dhanAccessToken,
          });
          return { success: true };
        } else {
          setError(data.message || "Failed to store credentials");
          return { success: false, error: data.message };
        }
      } catch (err: any) {
        setError(err.message || "Network error");
        return { success: false, error: err.message };
      } finally {
        setLoading(false);
      }
    },
    [userId]
  );

  // Fetch account data from Cloud Function
  const fetchAccountDataMethod = useCallback(
    async (forceRefresh = false) => {
      if (!userId || !credentials) {
        setAccountData(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const data = await fetchAccountDataAPI(
          userId,
          credentials.dhan_client_id,
          credentials.dhan_access_token
        );

        if (data) {
          setAccountData(data);
        } else {
          setError("Failed to fetch account data");
          setAccountData(null);
        }
      } catch (err: any) {
        setError(err.message || "Network error");
        setAccountData(null);
      } finally {
        setLoading(false);
      }
    },
    [userId, credentials]
  );

  // Auto-fetch credentials when userId changes
  useEffect(() => {
    if (userId) {
      fetchCredentials();
    }
  }, [userId, fetchCredentials]);

  // Auto-fetch account data when credentials are available
  useEffect(() => {
    if (credentials) {
      fetchAccountData();
    }
  }, [credentials, fetchAccountData]);

  return {
    credentials,
    accountData,
    loading,
    error,
    fetchCredentials,
    storeCredentials: storeCredentialsMethod,
    fetchAccountData: fetchAccountDataMethod,
    hasCredentials: !!credentials,
  };
}
