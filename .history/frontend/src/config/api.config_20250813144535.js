// src/config/api.config.js
// KbEye API Configuration - Using centralized config.js

import CONFIG from './config.js';

const API_CONFIG = {
    // Get environment info from central config
    getEnvironment() {
        return CONFIG.ENVIRONMENT;
    },

    // Get API base URL from central config
    getApiBaseUrl() {
        return CONFIG.API.BASE_URL;
    },

    // Get WebSocket base URL from central config
    getWebSocketBaseUrl() {
        return CONFIG.WEBSOCKET.BASE_URL;
    },

    // API Endpoints (using central config)
    ENDPOINTS: {
        // Service Management
        SERVICES: {
            LIST: CONFIG.ENDPOINTS.SERVICES.LIST,
            CREATE: CONFIG.ENDPOINTS.SERVICES.CREATE,
            GET_BY_ID: CONFIG.ENDPOINTS.SERVICES.GET_BY_ID,
            DELETE: CONFIG.ENDPOINTS.SERVICES.DELETE
        },

        // Monitoring
        MONITORING: {
            STATUS: CONFIG.ENDPOINTS.MONITORING.STATUS
        },

        // Logs
        LOGS: {
            GET_BY_SERVICE: CONFIG.ENDPOINTS.LOGS.GET_BY_SERVICE
        },

        // Alerts
        ALERTS: {
            LIST: CONFIG.ENDPOINTS.ALERTS.LIST
        },

        // Health Check
        HEALTH: {
            ROOT: CONFIG.ENDPOINTS.HEALTH.ROOT,
            HEALTH: CONFIG.ENDPOINTS.HEALTH.HEALTH
        }
    },

    // HTTP Configuration from central config
    HTTP: {
        TIMEOUT: CONFIG.API.TIMEOUT,
        RETRY_ATTEMPTS: CONFIG.API.RETRY_ATTEMPTS,
        RETRY_DELAY: CONFIG.API.RETRY_DELAY,
        HEADERS: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    },

    // WebSocket Configuration from central config
    WEBSOCKET: {
        // Get WebSocket URL dynamically
        getWebSocketUrl() {
            return CONFIG.getWebSocketUrl();
        },

        RECONNECT_INTERVAL: CONFIG.WEBSOCKET.RECONNECT_INTERVAL,
        MAX_RECONNECT_ATTEMPTS: CONFIG.WEBSOCKET.RECONNECT_ATTEMPTS,
        PING_INTERVAL: CONFIG.WEBSOCKET.HEARTBEAT_INTERVAL,

        MESSAGE_TYPES: {
            HEALTH_CHECK: 'health_check'
        }
    },

    // Feature Flags from central config
    FEATURES: {
        WEBSOCKET_ENABLED: CONFIG.FEATURES.WEBSOCKET,
        AUTO_REFRESH_ENABLED: CONFIG.FEATURES.AUTO_REFRESH,
        NOTIFICATIONS_ENABLED: CONFIG.FEATURES.NOTIFICATIONS,
        DARK_MODE_ENABLED: CONFIG.FEATURES.DARK_MODE
    },

    // Debug settings from central config
    DEBUG: {
        ENABLED: CONFIG.DEBUG.ENABLED,
        LOG_LEVEL: CONFIG.DEBUG.LOG_LEVEL,
        LOG_API_CALLS: CONFIG.DEBUG.LOG_API_CALLS
    },

    // Default parameters for API calls
    DEFAULT_PARAMS: {
        LOGS_LINES: 50,
        ALERTS_LIMIT: 50
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
    }
};

// Utility function for building URLs (using central config)
API_CONFIG.buildUrl = function (endpoint, params = {}) {
    return CONFIG.buildUrl(endpoint, params);
};

// Debug logging for development
if (API_CONFIG.DEBUG.ENABLED) {
    console.log('🔧 API_CONFIG loaded with central configuration:', {
        environment: API_CONFIG.getEnvironment(),
        apiBaseUrl: API_CONFIG.getApiBaseUrl(),
        wsBaseUrl: API_CONFIG.getWebSocketBaseUrl(),
        features: API_CONFIG.FEATURES
    });
}

// Export the configuration
export default API_CONFIG;