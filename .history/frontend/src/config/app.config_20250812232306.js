// src/config/app.config.js
// KbEye Application Configuration

const APP_CONFIG = {
    // Application Information
    APP: {
        NAME: 'KbEye',
        VERSION: '1.0.0',
        DESCRIPTION: 'Microservices Monitoring Dashboard',
        AUTHOR: 'KbEye Team'
    },

    // UI Configuration
    UI: {
        // Theme settings
        THEME: {
            DEFAULT: 'dark',
            AVAILABLE: ['dark', 'light']
        },

        // Dashboard refresh intervals (in milliseconds)
        REFRESH_INTERVALS: {
            SERVICES_STATUS: 5000,    // 5 seconds
            LOGS: 10000,              // 10 seconds
            ALERTS: 15000,            // 15 seconds
            METRICS: 3000             // 3 seconds
        },

        // Pagination settings
        PAGINATION: {
            DEFAULT_PAGE_SIZE: 20,
            MAX_PAGE_SIZE: 100,
            AVAILABLE_SIZES: [10, 20, 50, 100]
        },

        // Grid settings
        GRID: {
            SERVICES_PER_ROW: {
                DESKTOP: 4,
                TABLET: 2,
                MOBILE: 1
            },
            MIN_CARD_WIDTH: 280,
            CARD_GAP: 16
        },

        // Animation settings
        ANIMATIONS: {
            ENABLED: true,
            DURATION: {
                FAST: 200,
                NORMAL: 300,
                SLOW: 500
            }
        }
    },

    // Real-time Updates
    REALTIME: {
        // Auto-refresh settings
        AUTO_REFRESH: {
            ENABLED: true,
            INTERVAL: 5000, // 5 seconds
            PAUSE_ON_BLUR: true
        },

        // WebSocket settings
        WEBSOCKET: {
            AUTO_RECONNECT: true,
            RECONNECT_DELAY: 3000,
            MAX_RECONNECT_ATTEMPTS: 5,
            HEARTBEAT_INTERVAL: 30000
        },

        // Notification settings
        NOTIFICATIONS: {
            ENABLED: true,
            DURATION: 5000, // 5 seconds
            MAX_VISIBLE: 3,
            POSITION: 'top-right' // top-left, top-right, bottom-left, bottom-right
        }
    },

    // Data Management
    DATA: {
        // Local storage keys
        STORAGE_KEYS: {
            THEME: 'kbeye_theme',
            USER_PREFERENCES: 'kbeye_preferences',
            DASHBOARD_LAYOUT: 'kbeye_layout',
            FILTERS: 'kbeye_filters'
        },

        // Cache settings
        CACHE: {
            SERVICES_TTL: 60000,      // 1 minute
            LOGS_TTL: 30000,          // 30 seconds
            ALERTS_TTL: 60000,        // 1 minute
            MAX_CACHE_SIZE: 100       // Maximum cached items
        },

        // Data limits
        LIMITS: {
            MAX_LOG_ENTRIES: 1000,
            MAX_ALERT_HISTORY: 500,
            MAX_METRICS_POINTS: 100
        }
    },

    // Service Health Definitions
    HEALTH: {
        STATUS_TYPES: {
            HEALTHY: 'healthy',
            UNHEALTHY: 'unhealthy',
            UNKNOWN: 'unknown',
            LOADING: 'loading'
        },

        RESPONSE_TIME_THRESHOLDS: {
            EXCELLENT: 100,   // < 100ms
            GOOD: 500,        // < 500ms
            POOR: 2000,       // < 2s
            CRITICAL: 5000    // >= 5s
        },

        STATUS_COLORS: {
            HEALTHY: '#2ed573',
            UNHEALTHY: '#ff4757',
            UNKNOWN: '#8892b0',
            LOADING: '#00d4ff'
        }
    },

    // Alert Definitions
    ALERTS: {
        SEVERITY_LEVELS: {
            LOW: 'low',
            MEDIUM: 'medium',
            HIGH: 'high',
            CRITICAL: 'critical'
        },

        SEVERITY_COLORS: {
            LOW: '#ffa502',
            MEDIUM: '#ff7675',
            HIGH: '#fd79a8',
            CRITICAL: '#ff4757'
        },

        TYPES: {
            SERVICE_DOWN: 'service_down',
            SERVICE_SLOW: 'service_slow',
            SERVICE_ERROR: 'service_error',
            CONNECTION_LOST: 'connection_lost'
        }
    },

    // Logging Configuration
    LOGGING: {
        LEVEL: 'info', // debug, info, warn, error
        MAX_LOG_SIZE: 1000,
        PERSIST_LOGS: false,
        
        LOG_LEVELS: {
            DEBUG: 0,
            INFO: 1,
            WARN: 2,
            ERROR: 3
        }
    },

    // Feature Flags
    FEATURES: {
        DARK_MODE: true,
        REAL_TIME_UPDATES: true,
        WEBSOCKET_CONNECTION: true,
        NOTIFICATIONS: true,
        LOCAL_STORAGE: true,
        EXPORT_DATA: true,
        ADVANCED_FILTERING: true,
        METRICS_CHARTS: true
    },

    // Development Settings
    DEV: {
        DEBUG_MODE: false,
        MOCK_DATA: false,
        LOG_API_CALLS: false,
        SHOW_PERFORMANCE_METRICS: false
    }
};

// Utility functions
APP_CONFIG.getRefreshInterval = function(type) {
    return this.UI.REFRESH_INTERVALS[type.toUpperCase()] || 5000;
};

APP_CONFIG.getStatusColor = function(status) {
    return this.HEALTH.STATUS_COLORS[status.toUpperCase()] || this.HEALTH.STATUS_COLORS.UNKNOWN;
};

APP_CONFIG.getSeverityColor = function(severity) {
    return this.ALERTS.SEVERITY_COLORS[severity.toUpperCase()] || this.ALERTS.SEVERITY_COLORS.LOW;
};

APP_CONFIG.isFeatureEnabled = function(feature) {
    return this.FEATURES[feature.toUpperCase()] === true;
};

// Export the configuration
export default APP_CONFIG;