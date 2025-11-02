// Quick fixes for InfinityAI.Pro dashboard issues
// Add this to your frontend to handle errors gracefully

// 1. AI Analysis Error Handler
function handleAiAnalysisError() {
    const aiAnalysisElement = document.querySelector('[data-testid="ai-analysis"]');
    if (aiAnalysisElement) {
        aiAnalysisElement.innerHTML = `
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div class="flex items-center">
                    <div class="text-yellow-500 text-xl mr-3">⚠️</div>
                    <div>
                        <h3 class="text-yellow-800 font-medium">AI Analysis Temporarily Unavailable</h3>
                        <p class="text-yellow-600 text-sm mt-1">
                            We're working to restore the AI analysis service. Please check back in a few minutes.
                        </p>
                        <button onclick="location.reload()" 
                                class="mt-2 px-3 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600">
                            Refresh Page
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
}

// 2. Engine Status Error Handler
function handleEngineErrors() {
    const engineElements = document.querySelectorAll('[data-engine-status="error"]');
    engineElements.forEach(element => {
        element.innerHTML = `
            <div class="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded">
                <div class="flex items-center">
                    <div class="w-3 h-3 bg-red-500 rounded-full mr-3"></div>
                    <span class="text-red-800">Engine Temporarily Unavailable</span>
                </div>
                <button onclick="checkEngineStatus(this)" 
                        class="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600">
                    Retry
                </button>
            </div>
        `;
    });
}

// 3. WebSocket Connection Handler
function initWebSocketWithFallback() {
    const wsUrl = 'wss://infinityai-engine-d-ckxt6xvshq-uc.a.run.app/ws/dashboard';
    let ws;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    function connect() {
        try {
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log('✅ WebSocket connected');
                reconnectAttempts = 0;
                updateConnectionStatus(true);
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                } catch (e) {
                    console.error('❌ WebSocket message error:', e);
                }
            };
            
            ws.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                updateConnectionStatus(false);
                
                if (reconnectAttempts < maxReconnectAttempts) {
                    setTimeout(() => {
                        reconnectAttempts++;
                        connect();
                    }, 1000 * Math.pow(2, reconnectAttempts));
                }
            };
            
            ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('❌ WebSocket connection failed:', error);
            updateConnectionStatus(false);
        }
    }
    
    function updateConnectionStatus(connected) {
        const statusElement = document.querySelector('[data-connection-status]');
        if (statusElement) {
            statusElement.innerHTML = connected 
                ? '<span class="text-green-500 text-sm">● Live</span>'
                : '<span class="text-red-500 text-sm">● Disconnected</span>';
        }
    }
    
    connect();
}

// 4. Auto-retry Failed Components
function autoRetryFailedComponents() {
    setInterval(() => {
        // Retry AI analysis if showing error
        const errorElements = document.querySelectorAll('[data-component-error="true"]');
        if (errorElements.length > 0) {
            console.log('🔄 Auto-retrying failed components...');
            errorElements.forEach(element => {
                const retryButton = element.querySelector('button[onclick*="retry"]');
                if (retryButton) {
                    retryButton.click();
                }
            });
        }
    }, 60000); // Retry every minute
}

// 5. Initialize all fixes
function initDashboardFixes() {
    console.log('🔧 Initializing dashboard fixes...');
    
    // Handle existing errors
    handleAiAnalysisError();
    handleEngineErrors();
    
    // Initialize WebSocket with fallback
    initWebSocketWithFallback();
    
    // Start auto-retry mechanism
    autoRetryFailedComponents();
    
    console.log('✅ Dashboard fixes initialized');
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboardFixes);
} else {
    initDashboardFixes();
}
