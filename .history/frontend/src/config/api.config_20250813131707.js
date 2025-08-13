// src/config/api.config.js
// KbEye API Configuration with Environment Variables

const API_CONFIG = {
    // Environment-based configuration
    getEnvironment() {
        return import.meta.env.VITE_APP_ENV || 'development';
    },

    // Get API base URL from environment
    getApiBaseUrl() {
        const baseUrl = import.meta.env.VITE_API_BASE_URL;
        if (!baseUrl) {
            console.warn('⚠️ VITE_API_BASE_URL not found, falling back to localhost:8000');
            return 'http://localhost:8000';
        }
        return baseUrl;
    },

    // Get WebSocket base URL from environment  
    getWebSocketBaseUrl() {
        const wsUrl = import.meta.env.VITE_WS_BASE_URL;
        if (!wsUrl) {
            console.warn('⚠️ VITE_WS_BASE_URL not found, falling back to ws://localhost:8000');
            return 'ws://localhost:8000';
        }
        return wsUrl;
    },

    // API Endpoints (using environment variables)
    ENDPOINTS: {
        // Service Management
        SERVICES: {
            LIST: `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/services/`,
            CREATE: `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/services/`,
            GET_BY_ID: (serviceId) => `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/services/${serviceId}`,
            DELETE: (serviceId) => `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/services/${serviceId}`
        },

        // Monitoring
        MONITORING: {
            STATUS: `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/monitoring/status`
        },

        // Logs
        LOGS: {
            GET_BY_SERVICE: (serviceId, lines = 50) => `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/logs/${serviceId}?lines=${lines}`
        },

        // Alerts
        ALERTS: {
            LIST: (limit = 50) => `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/alerts/?limit=${limit}`
        },

        // Configuration
        CONFIG: {
            SERVICES: `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/config/services`,
            SYNC: `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/config/sync`,
            EXPORT: `${import.meta.env.VITE_API_BASE_PATH || '/api/v1'}/config/export`
        },

        // Health Check
        HEALTH: {
            ROOT: '/',
            HEALTH: '/health'
        }
    },

    // Default query parameters (from environment or defaults)
    DEFAULT_PARAMS: {
        LOGS_LINES: parseInt(import.meta.env.VITE_DEFAULT_LOG_LINES) || 50,
        ALERTS_LIMIT: parseInt(import.meta.env.VITE_DEFAULT_ALERTS_LIMIT) || 50,
        SERVICE_TIMEOUT: parseInt(import.meta.env.VITE_DEFAULT_TIMEOUT) || 5000,
        CHECK_INTERVAL: parseInt(import.meta.env.VITE_DEFAULT_CHECK_INTERVAL) || 30
    },

    // HTTP Configuration (from environment or defaults)
    HTTP: {
        TIMEOUT: parseInt(import.meta.env.VITE_HTTP_TIMEOUT) || 10000,
        RETRY_ATTEMPTS: parseInt(import.meta.env.VITE_HTTP_RETRY_ATTEMPTS) || 3,
        RETRY_DELAY: parseInt(import.meta.env.VITE_HTTP_RETRY_DELAY) || 1000,
        HEADERS: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    },

    // WebSocket Configuration (from environment)
    WEBSOCKET: {
        // Get WebSocket URL dynamically
        getWebSocketUrl() {
            const baseUrl = this.getWebSocketBaseUrl();
            const endpointPath = import.meta.env.VITE_WS_ENDPOINT_PATH || '/ws';
            return `${baseUrl}${endpointPath}`;
        },

        RECONNECT_INTERVAL: parseInt(import.meta.env.VITE_WS_RECONNECT_INTERVAL) || 3000,
        MAX_RECONNECT_ATTEMPTS: parseInt(import.meta.env.VITE_WS_RECONNECT_ATTEMPTS) || 5,
        PING_INTERVAL: parseInt(import.meta.env.VITE_WS_HEARTBEAT_INTERVAL) || 30000,
        
        MESSAGE_TYPES: {
            HEALTH_CHECK: 'health_check'
        }
    },

    // Response Status Codes
    STATUS_CODES: {
        SUCCESS: 200,
        BAD_REQUEST: 400,
        NOT_FOUND: 404,
        INTERNAL_ERROR: 500,
        BAD_GATEWAY: 502,
        GATEWAY_TIMEOUT: 504
    },

    // Error Messages
    ERROR_MESSAGES: {
        NETWORK_ERROR: 'Network connection failed',
        TIMEOUT: 'Request timeout',
        SERVICE_NOT_FOUND: 'Service not found',
        VALIDATION_ERROR: 'Validation failed',
        UNKNOWN_ERROR: 'An unknown error occurred'
    },

    // Feature Flags (from environment)
    FEATURES: {
        WEBSOCKET_ENABLED: import.meta.env.VITE_ENABLE_WEBSOCKET === 'true',
        AUTO_REFRESH_ENABLED: import.meta.env.VITE_ENABLE_AUTO_REFRESH === 'true',
        NOTIFICATIONS_ENABLED: import.meta.env.VITE_ENABLE_NOTIFICATIONS === 'true',
        DARK_MODE_ENABLED: import.meta.env.VITE_ENABLE_DARK_MODE === 'true'
    },

    // Development/Debug settings
    DEBUG: {
        ENABLED: import.meta.env.VITE_DEBUG_MODE === 'true',
        LOG_LEVEL: import.meta.env.VITE_LOG_LEVEL || 'info',
        LOG_API_CALLS: import.meta.env.VITE_LOG_API_CALLS === 'true'
    }
};

// Utility functions for building URLs
API_CONFIG.buildUrl = function(endpoint, params = {}) {
    let url = this.getApiBaseUrl() + endpoint;
    
    // Add query parameters if provided
    const queryParams = new URLSearchParams(params).toString();
    if (queryParams) {
        url += (url.includes('?') ? '&' : '?') + queryParams;
    }
    
    return url;
};

// Debug logging for development
if (API_CONFIG.DEBUG.ENABLED) {
    console.log('🔧 KbEye API Configuration:', {
        environment: API_CONFIG.getEnvironment(),
        apiBaseUrl: API_CONFIG.getApiBaseUrl(),
        wsBaseUrl: API_CONFIG.getWebSocketBaseUrl(),
        features: API_CONFIG.FEATURES
    });
}

// Export the configuration
export default API_CONFIG;