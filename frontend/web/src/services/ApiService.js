/**
 * Determines the appropriate base URL for API calls.
 * In production, it uses the main domain. In development, it falls back to a local server.
 * @returns {string} The base URL for the API.
 */
const getBaseUrl = () => {
    if (process.env.NODE_ENV === 'production') {
        // In production, all calls go through the main domain/CloudFront
        return 'https://infinityai.pro';
    }
    // For local development, you can point this to your local backend aggregator service
    return process.env.REACT_APP_API_URL || 'http://localhost:8003';
};

const API_BASE_URL = getBaseUrl();

/**
 * A centralized and simplified function to make API requests.
 * It automatically prepends the correct base URL and handles JSON parsing and errors.
 *
 * @param {string} endpoint - The API endpoint to call (e.g., '/engine-d/status').
 * @param {object} options - Optional fetch options (method, headers, body, etc.).
 * @returns {Promise<any>} - A promise that resolves with the JSON response.
 * @throws {Error} - Throws an error if the network request fails or the response is not ok.
 */
export const callApi = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
        // Add any other default headers here, like Authorization tokens
    };

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'API request failed with status ' + response.status }));
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        // Handle cases where the response might be empty
        const text = await response.text();
        return text ? JSON.parse(text) : {};

    } catch (error) {
        console.error(`API call to ${endpoint} failed:`, error);
        throw error; // Re-throw the error to be handled by the calling component
    }
};

// --- Service-Specific API Functions ---

/**
 * Fetches the master system health status from the aggregator engine.
 */
export const getSystemHealth = () => callApi('/engine-d/status');

/**
 * Fetches live market data for the dashboard.
 */
export const getMarketData = () => callApi('/engine-d/market-data');

/**
 * Fetches AI-generated insights.
 */
export const getAiInsights = () => callApi('/engine-a/insights');

/**
 * Fetches the user's portfolio data.
 * @param {string} userId - The ID of the user.
 */
export const getPortfolio = (userId) => callApi(`/engine-c/portfolio/${userId}`);

/**
 * Sends a message to the AI chatbot and gets a response.
 * @param {string} message - The user's message.
 * @param {string} userId - The ID of the user.
 */
export const sendChatMessage = (message, userId) => {
    return callApi('/engine-a/chat', {
        method: 'POST',
        body: JSON.stringify({ message, user_id: userId }),
    });
};

/**
 * Fetches the current Dhan settings and URLs.
 * @param {string} userId - The ID of the user.
 */
export const getDhanSettings = (userId) => callApi(`/engine-b/settings/${userId}`);

/**
 * Updates the Dhan credentials.
 * @param {object} credentials - The credentials to save.
 * @param {string} credentials.clientId - The Dhan client ID.
 * @param {string} credentials.accessToken - The Dhan access token.
 * @param {string} userId - The ID of the user.
 */
export const updateDhanSettings = (credentials, userId) => {
    return callApi(`/engine-b/settings/${userId}`, {
        method: 'POST',
        body: JSON.stringify(credentials),
    });
};
