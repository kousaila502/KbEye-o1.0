// frontend/src/config/config.js
// KbEye Frontend - Simple Centralized Configuration
// Single source of truth for all frontend settings

// =============================================================================
// ENVIRONMENT PRESETS - Easy switching between environments
// =============================================================================

const ENVIRONMENT_PRESETS = {
  // Development (localhost)
  development: {
    API_BASE_URL: 'http://localhost:8000',
    WS_BASE_URL: 'ws://localhost:8000',
    DEBUG_MODE: true,
    LOG_LEVEL: 'info'
  },

  // Production 
  production: {
    API_BASE_URL: 'https://api.yourdomain.com',
    WS_BASE_URL: 'wss://api.yourdomain.com',
    DEBUG_MODE: false,
    LOG_LEVEL: 'error'
  },

  // Staging
  staging: {
    API_BASE_URL: 'https://staging-api.yourdomain.com',
    WS_BASE_URL: 'wss://staging-api.yourdomain.com',
    DEBUG_MODE: true,
    LOG_LEVEL: 'warn'
  },

  // Docker Development
  docker: {
    API_BASE_URL: 'http://kbeye-backend:8000',
    WS_BASE_URL: 'ws://kbeye-backend:8000',
    DEBUG_MODE: true,
    LOG_LEVEL: 'info'
  }
};

// =============================================================================
// CURRENT ENVIRONMENT DETECTION
// =============================================================================

const CURRENT_ENV = import.meta.env.VITE_APP_ENV || 'development';
const PRESET = ENVIRONMENT_PRESETS[CURRENT_ENV] || ENVIRONMENT_PRESETS.development;

// =============================================================================
// MAIN CONFIGURATION - Override with .env.local or use presets
// =============================================================================

const CONFIG = {

  // =============================================================================
  // BASIC SETTINGS
  // =============================================================================

  ENVIRONMENT: CURRENT_ENV,

  APP: {
    NAME: import.meta.env.VITE_APP_NAME || 'KbEye',
    VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
    DESCRIPTION: 'Microservices Monitoring Dashboard'
  },

  // =============================================================================
  // NETWORK & URLs
  // =============================================================================

  API: {
    BASE_URL: import.meta.env.VITE_API_BASE_URL || PRESET.API_BASE_URL,
    BASE_PATH: import.meta.env.VITE_API_BASE_PATH || '/api/v1',
    TIMEOUT: parseInt(import.meta.env.VITE_HTTP_TIMEOUT) || 10000,
    RETRY_ATTEMPTS: parseInt(import.meta.env.VITE_HTTP_RETRY_ATTEMPTS) || 3,
    RETRY_DELAY: parseInt(import.meta.env.VITE_HTTP_RETRY_DELAY) || 1000
  },

  WEBSOCKET: {
    BASE_URL: import.meta.env.VITE_WS_BASE_URL || PRESET.WS_BASE_URL,
    ENDPOINT_PATH: import.meta.env.VITE_WS_ENDPOINT_PATH || '/ws',
    RECONNECT_ATTEMPTS: parseInt(import.meta.env.VITE_WS_RECONNECT_ATTEMPTS) || 5,
    RECONNECT_INTERVAL: parseInt(import.meta.env.VITE_WS_RECONNECT_INTERVAL) || 3000,
    HEARTBEAT_INTERVAL: parseInt(import.meta.env.VITE_WS_HEARTBEAT_INTERVAL) || 25000,
    GRACE_PERIOD: parseInt(import.meta.env.VITE_WS_GRACE_PERIOD) || 10000
  },

  // =============================================================================
  // FEATURES - Easy to enable/disable
  // =============================================================================

  FEATURES: {
    WEBSOCKET: import.meta.env.VITE_ENABLE_WEBSOCKET !== 'false',
    AUTO_REFRESH: import.meta.env.VITE_ENABLE_AUTO_REFRESH !== 'false',
    NOTIFICATIONS: import.meta.env.VITE_ENABLE_NOTIFICATIONS !== 'false',
    DARK_MODE: import.meta.env.VITE_ENABLE_DARK_MODE !== 'false'
  },

  // =============================================================================
  // TIMING SETTINGS
  // =============================================================================

  REFRESH_INTERVALS: {
    SERVICES: parseInt(import.meta.env.VITE_REFRESH_INTERVAL_SERVICES) || 5000,
    LOGS: parseInt(import.meta.env.VITE_REFRESH_INTERVAL_LOGS) || 10000,
    ALERTS: parseInt(import.meta.env.VITE_REFRESH_INTERVAL_ALERTS) || 15000
  },

  // =============================================================================
  // DEBUG SETTINGS
  // =============================================================================

  DEBUG: {
    ENABLED: import.meta.env.VITE_DEBUG_MODE === 'true' || PRESET.DEBUG_MODE,
    LOG_LEVEL: import.meta.env.VITE_LOG_LEVEL || PRESET.LOG_LEVEL,
    LOG_API_CALLS: import.meta.env.VITE_LOG_API_CALLS === 'true'
  },

  // =============================================================================
  // API ENDPOINTS - Built from base config
  // =============================================================================

  ENDPOINTS: {
    // Services
    SERVICES: {
      LIST: '/services/',
      CREATE: '/services/',
      GET_BY_ID: (id) => `/services/${id}`,
      DELETE: (id) => `/services/${id}`
    },

    // Monitoring
    MONITORING: {
      STATUS: '/monitoring/status'
    },

    // Logs
    LOGS: {
      GET_BY_SERVICE: (serviceId, lines = 50) => `/logs/${serviceId}?lines=${lines}`
    },

    // Alerts
    ALERTS: {
      LIST: (limit = 50) => `/alerts/?limit=${limit}`
    },

    // Health
    HEALTH: {
      ROOT: '/',
      HEALTH: '/health'
    }
  },

  // =============================================================================
  // HELPER METHODS - Make it easy to use
  // =============================================================================

  // Get full API URL
  getApiUrl(endpoint = '') {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

    console.log('🔄 Testing HTTP API connection...');

    // ADD THIS LOG:
    console.log('🔍 Health endpoint URL:', this.buildUrl('/health'));
    return `${this.API.BASE_URL}${this.API.BASE_PATH}${cleanEndpoint}`;
  },

  // Get WebSocket URL
  getWebSocketUrl() {
    return `${this.WEBSOCKET.BASE_URL}${this.WEBSOCKET.ENDPOINT_PATH}`;
  },

  // Build URL with query parameters
  buildUrl(endpoint, params = {}) {
    let url = this.getApiUrl(endpoint);
    const queryParams = new URLSearchParams(params).toString();
    if (queryParams) {
      url += (url.includes('?') ? '&' : '?') + queryParams;
    }
    return url;
  },

  // Check if feature is enabled
  isFeatureEnabled(feature) {
    return this.FEATURES[feature.toUpperCase()] === true;
  },

  // Get refresh interval
  getRefreshInterval(type) {
    return this.REFRESH_INTERVALS[type.toUpperCase()] || 5000;
  },

  // Get current environment summary
  getSummary() {
    return {
      environment: this.ENVIRONMENT,
      apiUrl: this.API.BASE_URL,
      wsUrl: this.WEBSOCKET.BASE_URL,
      debugMode: this.DEBUG.ENABLED,
      features: Object.keys(this.FEATURES).filter(key => this.FEATURES[key])
    };
  }
};

// =============================================================================
// DEBUG OUTPUT
// =============================================================================

if (CONFIG.DEBUG.ENABLED) {
  console.group('🔧 KbEye Frontend Configuration');
  console.log('Environment:', CONFIG.ENVIRONMENT);
  console.log('API URL:', CONFIG.API.BASE_URL);
  console.log('WebSocket URL:', CONFIG.getWebSocketUrl());
  console.log('Features:', Object.keys(CONFIG.FEATURES).filter(key => CONFIG.FEATURES[key]));
  console.log('Preset Used:', CURRENT_ENV in ENVIRONMENT_PRESETS ? 'Yes' : 'Custom');
  console.groupEnd();
}

export default CONFIG;