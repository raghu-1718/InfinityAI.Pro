
const YOUR_BACKEND_TOKEN_EXCHANGE_URL = 'https://api.infinityai.pro/exchange-dhan-token';

export const exchangeAuthCodeForToken = async (authCode: string) => {
  try {
    const response = await fetch(YOUR_BACKEND_TOKEN_EXCHANGE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ authCode }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Token exchange failed: ${errorData.error || 'Unknown error'}`);
    }

    const tokenData = await response.json();
    return tokenData; // { accessToken: '...', refreshToken: '...' }
  } catch (error) {
    console.error('Error exchanging auth code for token:', error);
    throw error;
  }
};
