// src/services/websocket.service.js
// KbEye WebSocket Service for Real-time Updates

import API_CONFIG from '../config/api.config.js';

class WebSocketService {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = API_CONFIG.WEBSOCKET.MAX_RECONNECT_ATTEMPTS;
        this.reconnectInterval = API_CONFIG.WEBSOCKET.RECONNECT_INTERVAL;
        this.isConnecting = false;
        this.isManualDisconnect = false;
        
        // Event listeners
        this.listeners = {
            open: [],
            close: [],
            error: [],
            message: [],
            healthCheck: []
        };
    }

    // Connect to WebSocket
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('🔌 WebSocket already connected');
            return Promise.resolve();
        }

        if (this.isConnecting) {
            console.log('🔌 WebSocket connection already in progress');
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            try {
                this.isConnecting = true;
                this.isManualDisconnect = false;
                
                const wsUrl = API_CONFIG.WEBSOCKET.getWebSocketUrl();
                console.log('🔌 Connecting to WebSocket:', wsUrl);
                
                this.ws = new WebSocket(wsUrl);

                // Connection opened
                this.ws.onopen = (event) => {
                    console.log('✅ WebSocket connected successfully');
                    this.isConnecting = false;
                    this.reconnectAttempts = 0;
                    this.emitEvent('open', event);
                    resolve();
                };

                // Message received
                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('📨 WebSocket message received:', data);
                        
                        this.emitEvent('message', data);
                        
                        // Handle specific message types
                        if (data.type === API_CONFIG.WEBSOCKET.MESSAGE_TYPES.HEALTH_CHECK) {
                            this.emitEvent('healthCheck', data.data);
                        }
                    } catch (error) {
                        console.error('❌ Error parsing WebSocket message:', error);
                        console.log('Raw message:', event.data);
                        
                        // Handle non-JSON messages (like echo responses)
                        this.emitEvent('message', event.data);
                    }
                };

                // Connection closed
                this.ws.onclose = (event) => {
                    console.log('🔌 WebSocket connection closed:', event.code, event.reason);
                    this.isConnecting = false;
                    this.emitEvent('close', event);
                    
                    // Attempt reconnection if not manually disconnected
                    if (!this.isManualDisconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.scheduleReconnection();
                    }
                };

                // Connection error
                this.ws.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    this.isConnecting = false;
                    this.emitEvent('error', error);
                    reject(error);
                };

            } catch (error) {
                console.error('❌ WebSocket connection failed:', error);
                this.isConnecting = false;
                reject(error);
            }
        });
    }

    // Disconnect WebSocket
    disconnect() {
        console.log('🔌 Manually disconnecting WebSocket');
        this.isManualDisconnect = true;
        
        if (this.ws) {
            this.ws.close(1000, 'Manual disconnect');
            this.ws = null;
        }
    }

    // Schedule reconnection attempt
    scheduleReconnection() {
        this.reconnectAttempts++;
        const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
        
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

    // Send message to WebSocket
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
                this.ws.send(messageStr);
                console.log('📤 WebSocket message sent:', messageStr);
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

    // Get reconnection info
    getReconnectionInfo() {
        return {
            attempts: this.reconnectAttempts,
            maxAttempts: this.maxReconnectAttempts,
            isReconnecting: this.reconnectAttempts > 0 && this.reconnectAttempts <= this.maxReconnectAttempts
        };
    }

    // Test WebSocket with ping
    ping() {
        return this.send('ping');
    }
}

// Create and export singleton instance
const wsService = new WebSocketService();
export default wsService;