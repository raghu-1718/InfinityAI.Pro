import { getEngineCUrl } from "@/lib/api";

const ENGINE_C_URL = getEngineCUrl();

async function postJson(path: string, body: Record<string, unknown>) {
  const response = await fetch(`${ENGINE_C_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

export async function verifyCouponAPI(
  couponCode: string,
  userId: string,
  email: string
) {
  return postJson("/api/auth/coupon/verify", {
    coupon_code: couponCode,
    user_id: userId,
    email,
  });
}

export async function getCredentialsAPI(userId: string) {
  const response = await fetch(
    `${ENGINE_C_URL}/api/user/credentials?user_id=${encodeURIComponent(userId)}`
  );
  return response.json();
}

export async function storeCredentialsAPI(
  userId: string,
  dhanClientId: string,
  dhanAccessToken: string
) {
  return postJson("/api/user/credentials", {
    user_id: userId,
    client_id: dhanClientId,
    access_token: dhanAccessToken,
  });
}

export async function fetchAccountDataAPI(
  userId: string,
  dhanClientId: string,
  dhanAccessToken: string
) {
  return postJson("/api/auth/account-data", {
    user_id: userId,
    dhan_client_id: dhanClientId,
    dhan_access_token: dhanAccessToken,
  });
}
