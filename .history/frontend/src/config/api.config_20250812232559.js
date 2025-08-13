// src/config/api.config.js
// KbEye API Configuration

const API_CONFIG = {
    // Base configuration
    BASE_URL: {
        development: 'http://localhost:8000',
        production: 'http://localhost:8000', // Update for production
        test: 'http://localhost:8000'
    },
    
    // Get current environment base URL
    getBaseUrl() {
        const env = import.meta.env.MODE || 'development';
        return this.BASE_URL[env] || this.BASE_URL.development;
    },

    // API Endpoints
    ENDPOINTS: {
        // Service Management
        SERVICES: {
            LIST: '/api/v1/services/',
            CREATE: '/api/v1/services/',
            GET_BY_ID: (serviceId) => `/api/v1/services/${serviceId}`,
            DELETE: (serviceId) => `/api/v1/services/${serviceId}`
        },

        // Monitoring
        MONITORING: {
            STATUS: '/api/v1/monitoring/status'
        },

        // Logs
        LOGS: {
            GET_BY_SERVICE: (serviceId, lines = 50) => `/api/v1/logs/${serviceId}?lines=${lines}`
        },

        // Alerts
        ALERTS: {
            LIST: (limit = 50) => `/api/v1/alerts/?limit=${limit}`
        },

        // Configuration
        CONFIG: {
            SERVICES: '/api/v1/config/services',
            SYNC: '/api/v1/config/sync',
            EXPORT: '/api/v1/config/export'
        },

        // Health Check
        HEALTH: {
            ROOT: '/',
            HEALTH: '/health'
        }
    },

    // Default query parameters
    DEFAULT_PARAMS: {
        LOGS_LINES: 50,
        ALERTS_LIMIT: 50,
        SERVICE_TIMEOUT: 5000,
        CHECK_INTERVAL: 30
    },

    // HTTP Configuration
    HTTP: {
        TIMEOUT: 10000, // 10 seconds
        RETRY_ATTEMPTS: 3,
        RETRY_DELAY: 1000, // 1 second
        HEADERS: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    },

    // WebSocket Configuration
    WEBSOCKET: {
        URL: {
            development: 'ws://localhost:8000/ws',
            production: 'ws://localhost:8000/ws', // Update for production
            test: 'ws://localhost:8000/ws'
        },
        
        getWebSocketUrl() {
            const env = import.meta.env.MODE || 'development';
            return this.URL[env] || this.URL.development;
        },

        RECONNECT_INTERVAL: 3000, // 3 seconds
        MAX_RECONNECT_ATTEMPTS: 5,
        PING_INTERVAL: 30000, // 30 seconds
        
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
    }
};

// Utility functions for building URLs
API_CONFIG.buildUrl = function(endpoint, params = {}) {
    let url = this.getBaseUrl() + endpoint;
    
    // Add query parameters if provided
    const queryParams = new URLSearchParams(params).toString();
    if (queryParams) {
        url += (url.includes('?') ? '&' : '?') + queryParams;
    }
    
    return url;
};

// Export the configuration
export default API_CONFIG;