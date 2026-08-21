// frontend/web-app/src/utils/api.ts

// Helper to determine Engine B URL based on environment
export const getEngineBUrl = () => {
  return (
    process.env.NEXT_PUBLIC_ENGINE_B_URL ||
    process.env.NEXT_PUBLIC_ENGINE_A_URL ||
    "https://engine-a-313407263327.asia-south1.run.app"
  );
};

export const fetchFromEngineB = async (endpoint: string, options: RequestInit = {}) => {
  // 1. Create a custom AbortController
  const controller = new AbortController();
  
  // 2. Set a generous 60-second timeout for Heavy AI operations
  const timeoutId = setTimeout(() => controller.abort(), 60000); 

  const baseUrl = getEngineBUrl();

  try {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      signal: controller.signal, // 3. Attach the custom signal
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    // 4. Clear the timeout if the request succeeds before 60 seconds
    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = new Error(`Engine-B API Error: ${response.statusText}`);
      (error as any).status = response.status;
      throw error;
    }

    return await response.json();
    
  } catch (error: any) {
    clearTimeout(timeoutId);
    
    // Catch the specific AbortError to log it cleanly
    if (error.name === 'AbortError') {
      console.error(`[TIMEOUT] Engine-B took longer than 60 seconds on ${endpoint}`);
      throw new Error('AI Engine timed out. Please try again.');
    }
    
    throw error;
  }
};
