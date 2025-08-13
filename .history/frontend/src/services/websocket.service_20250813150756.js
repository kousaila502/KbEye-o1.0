// src/services/websocket.service.js
// KbEye WebSocket Service with Environment Configuration

import API_CONFIG from '../config/api.config.js';

class WebSocketService {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = API_CONFIG.WEBSOCKET.MAX_RECONNECT_ATTEMPTS;
        this.reconnectInterval = API_CONFIG.WEBSOCKET.RECONNECT_INTERVAL;
        this.isManualDisconnect = false;
        this.pingInterval = null;
        this.pingIntervalTime = API_CONFIG.WEBSOCKET.PING_INTERVAL;
        
        // Grace period for connection status (from environment or default)
        this.disconnectionTimer = null;
        this.gracePeriod = parseInt(import.meta.env.VITE_WS_GRACE_PERIOD) || 10000; // 10 seconds default
        this.stableConnectionStatus = 'disconnected';
        
        // Event listeners
        this.listeners = {
            open: [],
            close: [],
            error: [],
            message: [],
            healthCheck: [],
            stableStatusChange: []
        };

        // Debug logging
        if (API_CONFIG.DEBUG.ENABLED) {
            //console.log('🔧 WebSocket Service initialized:', {
                wsUrl: API_CONFIG.WEBSOCKET.getWebSocketUrl(),
                maxReconnectAttempts: this.maxReconnectAttempts,
                reconnectInterval: this.reconnectInterval,
                gracePeriod: this.gracePeriod,
                enabled: API_CONFIG.FEATURES.WEBSOCKET_ENABLED
            });
        }
    }

    // Connect to WebSocket (using environment configuration)
    async connect() {
        // Check if WebSocket is enabled via feature flag
        if (!API_CONFIG.FEATURES.WEBSOCKET_ENABLED) {
            //console.log('🔌 WebSocket disabled via feature flag');
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            try {
                // Close existing connection if any
                if (this.ws) {
                    this.ws.close();
                }

                this.isManualDisconnect = false;
                
                // Get WebSocket URL from configuration (environment-aware)
                const wsUrl = API_CONFIG.WEBSOCKET.getWebSocketUrl();
                
                if (API_CONFIG.DEBUG.ENABLED) {
                    //console.log('🔌 Connecting to WebSocket:', wsUrl);
                }
                
                this.ws = new WebSocket(wsUrl);

                // Connection opened
                this.ws.onopen = (event) => {
                    //console.log('✅ WebSocket connected successfully');
                    this.reconnectAttempts = 0;
                    
                    // Clear disconnection timer and update stable status
                    this.clearDisconnectionTimer();
                    this.updateStableStatus('connected');
                    
                    this.emitEvent('open', event);
                    
                    // Start heartbeat to keep connection alive
                    this.startHeartbeat();
                    
                    // Test the connection
                    this.send('Frontend connected');
                    resolve();
                };

                // Message received
                this.ws.onmessage = (event) => {
                    if (API_CONFIG.DEBUG.ENABLED) {
                        //console.log('📨 WebSocket message received:', event.data);
                    }
                    
                    try {
                        // Try to parse as JSON first
                        const data = JSON.parse(event.data);
                        
                        this.emitEvent('message', data);
                        
                        // Handle health check messages
                        if (data.type === API_CONFIG.WEBSOCKET.MESSAGE_TYPES.HEALTH_CHECK) {
                            if (API_CONFIG.DEBUG.ENABLED) {
                                console.log('⚡ Health check update received:', data.data);
                            }
                            this.emitEvent('healthCheck', data.data);
                        }
                    } catch (error) {
                        // Handle plain text messages (echo responses)
                        if (API_CONFIG.DEBUG.ENABLED) {
                            console.log('📨 Text message:', event.data);
                        }
                        this.emitEvent('message', { type: 'echo', data: event.data });
                    }
                };

                // Connection closed
                this.ws.onclose = (event) => {
                    console.log('🔌 WebSocket connection closed:', event.code, event.reason);
                    this.stopHeartbeat();
                    
                    // Start grace period timer instead of immediate status change
                    this.startDisconnectionTimer();
                    
                    this.emitEvent('close', event);
                    
                    // Attempt reconnection if not manually disconnected
                    if (!this.isManualDisconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.scheduleReconnection();
                    }
                };

                // Connection error
                this.ws.onerror = (error) => {
                    console.error('❌ WebSocket error occurred:', error);
                    this.emitEvent('error', error);
                    
                    // Only reject on first connection attempt
                    if (this.reconnectAttempts === 0) {
                        reject(error);
                    }
                };

            } catch (error) {
                console.error('❌ WebSocket connection setup failed:', error);
                reject(error);
            }
        });
    }

    // Disconnect WebSocket
    disconnect() {
        console.log('🔌 Manually disconnecting WebSocket');
        this.isManualDisconnect = true;
        this.stopHeartbeat();
        this.clearDisconnectionTimer();
        this.updateStableStatus('disconnected');
        
        if (this.ws) {
            this.ws.close(1000, 'Manual disconnect');
            this.ws = null;
        }
    }

    // Schedule reconnection attempt
    scheduleReconnection() {
        this.reconnectAttempts++;
        const delay = this.reconnectInterval;
        
        console.log(`🔄 Scheduling WebSocket reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            if (!this.isManualDisconnect && this.reconnectAttempts <= this.maxReconnectAttempts) {
                console.log(`🔄 Attempting WebSocket reconnection (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect().catch(error => {
                    console.error('❌ WebSocket reconnection failed:', error);
                });
            }
        }, delay);
    }

    // Start heartbeat to keep connection alive (using environment configuration)
    startHeartbeat() {
        this.stopHeartbeat(); // Clear any existing interval
        
        this.pingInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                if (API_CONFIG.DEBUG.ENABLED) {
                    console.log('💓 Sending heartbeat ping');
                }
                this.send('ping');
            }
        }, this.pingIntervalTime);
    }

    // Stop heartbeat
    stopHeartbeat() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    // Start disconnection timer (grace period)
    startDisconnectionTimer() {
        this.clearDisconnectionTimer();
        
        if (API_CONFIG.DEBUG.ENABLED) {
            console.log(`⏳ Starting ${this.gracePeriod/1000}s grace period for WebSocket reconnection`);
        }
        
        this.disconnectionTimer = setTimeout(() => {
            console.log('⚠️ Grace period expired, marking as disconnected');
            this.updateStableStatus('disconnected');
        }, this.gracePeriod);
    }

    // Clear disconnection timer
    clearDisconnectionTimer() {
        if (this.disconnectionTimer) {
            if (API_CONFIG.DEBUG.ENABLED) {
                //console.log('✅ WebSocket reconnected within grace period');
            }
            clearTimeout(this.disconnectionTimer);
            this.disconnectionTimer = null;
        }
    }

    // Update stable connection status
    updateStableStatus(status) {
        if (this.stableConnectionStatus !== status) {
            console.log(`🔄 Stable WebSocket status changed: ${this.stableConnectionStatus} → ${status}`);
            this.stableConnectionStatus = status;
            this.emitEvent('stableStatusChange', status);
        }
    }

    // Get stable connection status (for UI)
    getStableConnectionStatus() {
        return this.stableConnectionStatus;
    }

    // Send message to WebSocket
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
                this.ws.send(messageStr);
                
                if (API_CONFIG.DEBUG.ENABLED) {
                    console.log('📤 WebSocket message sent:', messageStr);
                }
                return true;
            } catch (error) {
                console.error('❌ Failed to send WebSocket message:', error);
                return false;
            }
        } else {
            console.warn('⚠️ WebSocket not connected, cannot send message');
            return false;
        }
    }

    // Add event listener
    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        } else {
            console.warn(`⚠️ Unknown WebSocket event: ${event}`);
        }
    }

    // Remove event listener
    off(event, callback) {
        if (this.listeners[event]) {
            const index = this.listeners[event].indexOf(callback);
            if (index > -1) {
                this.listeners[event].splice(index, 1);
            }
        }
    }

    // Emit event to all listeners
    emitEvent(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`❌ Error in WebSocket ${event} listener:`, error);
                }
            });
        }
    }

    // Get connection status
    getConnectionStatus() {
        if (!this.ws) return 'disconnected';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'connecting';
            case WebSocket.OPEN:
                return 'connected';
            case WebSocket.CLOSING:
                return 'closing';
            case WebSocket.CLOSED:
                return 'disconnected';
            default:
                return 'unknown';
        }
    }

    // Check if connected
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    // Get configuration info (for debugging)
    getConfigInfo() {
        return {
            wsUrl: API_CONFIG.WEBSOCKET.getWebSocketUrl(),
            maxReconnectAttempts: this.maxReconnectAttempts,
            reconnectInterval: this.reconnectInterval,
            gracePeriod: this.gracePeriod,
            enabled: API_CONFIG.FEATURES.WEBSOCKET_ENABLED,
            stableStatus: this.stableConnectionStatus
        };
    }

    // Test connection with ping
    ping() {
        return this.send('ping');
    }
}

// Create and export singleton instance
const wsService = new WebSocketService();
export default wsService;