// src/services/api.service.js
// KbEye API Service - Handles all HTTP communication with backend

import API_CONFIG from '../config/api.config.js';

class ApiService {
    constructor() {
        this.baseUrl = API_CONFIG.getApiBaseUrl();
        this.defaultHeaders = API_CONFIG.HTTP.HEADERS;
        this.timeout = API_CONFIG.HTTP.TIMEOUT;
        this.retryAttempts = API_CONFIG.HTTP.RETRY_ATTEMPTS;
        this.retryDelay = API_CONFIG.HTTP.RETRY_DELAY;

        // Loading states
        this.loadingStates = new Map();
        this.requestQueue = new Map();
    }

    // Core HTTP method with retry logic
    async request(url, options = {}) {
        const requestId = this.generateRequestId();

        try {
            this.setLoading(requestId, true);

            const response = await this.makeRequestWithRetry(url, options);
            const data = await this.parseResponse(response);

            this.setLoading(requestId, false);
            return { success: true, data, status: response.status };

        } catch (error) {
            this.setLoading(requestId, false);
            return this.handleError(error);
        }
    }

    // Make request with automatic retry
    async makeRequestWithRetry(url, options, attempt = 1) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...this.defaultHeaders,
                    ...options.headers
                },
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return response;

        } catch (error) {
            clearTimeout(timeoutId);

            // Retry logic
            if (attempt < this.retryAttempts && this.shouldRetry(error)) {
                console.warn(`Request failed (attempt ${attempt}/${this.retryAttempts}). Retrying in ${this.retryDelay}ms...`);
                await this.delay(this.retryDelay);
                return this.makeRequestWithRetry(url, options, attempt + 1);
            }

            throw error;
        }
    }

    // Parse response based on content type
    async parseResponse(response) {
        const contentType = response.headers.get('content-type');

        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return await response.text();
    }

    // Error handling
    handleError(error) {
        let errorMessage = API_CONFIG.ERROR_MESSAGES.UNKNOWN_ERROR;

        if (error.name === 'AbortError') {
            errorMessage = API_CONFIG.ERROR_MESSAGES.TIMEOUT;
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = API_CONFIG.ERROR_MESSAGES.NETWORK_ERROR;
        } else if (error.message) {
            errorMessage = error.message;
        }

        console.error('API Error:', error);

        return {
            success: false,
            error: errorMessage,
            originalError: error
        };
    }

    // Determine if error should trigger retry
    shouldRetry(error) {
        if (error.name === 'AbortError') return false;
        if (error.message.includes('404')) return false;
        if (error.message.includes('400')) return false;
        return true;
    }

    // Utility methods
    generateRequestId() {
        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    setLoading(requestId, isLoading) {
        if (isLoading) {
            this.loadingStates.set(requestId, true);
        } else {
            this.loadingStates.delete(requestId);
        }

        // Emit loading state change event
        window.dispatchEvent(new CustomEvent('api:loading', {
            detail: { isLoading: this.loadingStates.size > 0 }
        }));
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // GET request
    async get(endpoint, params = {}) {
        const url = API_CONFIG.buildUrl(endpoint, params);
        return this.request(url, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data = null) {
        const url = API_CONFIG.buildUrl(endpoint);
        const options = {
            method: 'POST',
            body: data ? JSON.stringify(data) : null
        };
        return this.request(url, options);
    }

    // DELETE request
    async delete(endpoint) {
        const url = API_CONFIG.buildUrl(endpoint);
        return this.request(url, { method: 'DELETE' });
    }

    // =============================================================================
    // SERVICE-SPECIFIC API METHODS
    // =============================================================================

    // Services API
    async getServices() {
        return this.get(API_CONFIG.ENDPOINTS.SERVICES.LIST);
    }

    async createService(serviceData) {
        return this.post(API_CONFIG.ENDPOINTS.SERVICES.CREATE, serviceData);
    }

    async getService(serviceId) {
        return this.get(API_CONFIG.ENDPOINTS.SERVICES.GET_BY_ID(serviceId));
    }

    async deleteService(serviceId) {
        return this.delete(API_CONFIG.ENDPOINTS.SERVICES.DELETE(serviceId));
    }

    // Monitoring API
    async getServicesStatus() {
        return this.get(API_CONFIG.ENDPOINTS.MONITORING.STATUS);
    }

    // Logs API
    async getServiceLogs(serviceId, lines = null) {
        const logLines = lines || API_CONFIG.DEFAULT_PARAMS.LOGS_LINES;
        return this.get(API_CONFIG.ENDPOINTS.LOGS.GET_BY_SERVICE(serviceId, logLines));
    }

    // Alerts API
    async getAlerts(limit = null) {
        const alertLimit = limit || API_CONFIG.DEFAULT_PARAMS.ALERTS_LIMIT;
        return this.get(API_CONFIG.ENDPOINTS.ALERTS.LIST(alertLimit));
    }

    // Configuration API
    async getConfigServices() {
        return this.get(API_CONFIG.ENDPOINTS.CONFIG.SERVICES);
    }

    async syncConfig() {
        return this.post(API_CONFIG.ENDPOINTS.CONFIG.SYNC);
    }

    async exportConfig() {
        return this.get(API_CONFIG.ENDPOINTS.CONFIG.EXPORT);
    }

    // Health Check API
    async getHealth() {
        return this.get(API_CONFIG.ENDPOINTS.HEALTH.HEALTH);
    }

    async getRootStatus() {
        return this.get(API_CONFIG.ENDPOINTS.HEALTH.ROOT);
    }

    // =============================================================================
    // BATCH OPERATIONS
    // =============================================================================

    // Get dashboard data in one call
    async getDashboardData() {
        try {
            const [servicesResult, statusResult, alertsResult] = await Promise.allSettled([
                this.getServices(),
                this.getServicesStatus(),
                this.getAlerts(10) // Get last 10 alerts for dashboard
            ]);

            return {
                success: true,
                data: {
                    services: servicesResult.status === 'fulfilled' ? servicesResult.value.data : [],
                    status: statusResult.status === 'fulfilled' ? statusResult.value.data : [],
                    alerts: alertsResult.status === 'fulfilled' ? alertsResult.value.data : []
                },
                errors: {
                    services: servicesResult.status === 'rejected' ? servicesResult.reason : null,
                    status: statusResult.status === 'rejected' ? statusResult.reason : null,
                    alerts: alertsResult.status === 'rejected' ? alertsResult.reason : null
                }
            };
        } catch (error) {
            return this.handleError(error);
        }
    }

    // Test backend connectivity
    async testConnection() {
        try {
            const healthResult = await this.getHealth();
            if (healthResult.success) {
                return {
                    success: true,
                    message: 'Backend connection successful',
                    data: healthResult.data
                };
            } else {
                return {
                    success: false,
                    message: 'Backend connection failed',
                    error: healthResult.error
                };
            }
        } catch (error) {
            return {
                success: false,
                message: 'Backend unreachable',
                error: error.message
            };
        }
    }

    // =============================================================================
    // UTILITY METHODS
    // =============================================================================

    // Check if currently loading any requests
    isLoading() {
        return this.loadingStates.size > 0;
    }

    // Get current base URL
    // ...removed getBaseUrl utility method...

    // Update configuration (useful for environment switching)
    updateConfig(newConfig) {
        if (newConfig.baseUrl) this.baseUrl = newConfig.baseUrl;
        if (newConfig.timeout) this.timeout = newConfig.timeout;
        if (newConfig.retryAttempts) this.retryAttempts = newConfig.retryAttempts;
    }
}

// Create and export singleton instance
const apiService = new ApiService();
export default apiService;