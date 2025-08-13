// src/services/websocket.service.js
// KbEye WebSocket Service - Clean Working Version

import API_CONFIG from '../config/api.config.js';

class WebSocketService {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000;
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
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                // Close existing connection if any
                if (this.ws) {
                    this.ws.close();
                }

                this.isManualDisconnect = false;
                
                const wsUrl = 'ws://localhost:8000/ws'; // Direct URL for now
                console.log('🔌 Connecting to WebSocket:', wsUrl);
                
                this.ws = new WebSocket(wsUrl);

                // Connection opened
                this.ws.onopen = (event) => {
                    console.log('✅ WebSocket connected successfully');
                    this.reconnectAttempts = 0;
                    this.emitEvent('open', event);
                    
                    // Test the connection
                    this.send('Frontend connected');
                    resolve();
                };

                // Message received
                this.ws.onmessage = (event) => {
                    console.log('📨 WebSocket message received:', event.data);
                    
                    try {
                        // Try to parse as JSON
                        const data = JSON.parse(event.data);
                        console.log('📨 Parsed JSON message:', data);
                        
                        this.emitEvent('message', data);
                        
                        // Handle health check messages
                        if (data.type === 'health_check') {
                            console.log('⚡ Health check update received:', data.data);
                            this.emitEvent('healthCheck', data.data);
                        }
                    } catch (error) {
                        // Handle plain text messages (echo responses)
                        console.log('📨 Text message:', event.data);
                        this.emitEvent('message', { type: 'echo', data: event.data });
                    }
                };

                // Connection closed
                this.ws.onclose = (event) => {
                    console.log('🔌 WebSocket connection closed:', event.code, event.reason);
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

    // Test connection with ping
    ping() {
        return this.send('ping');
    }
}

// Create and export singleton instance
const wsService = new WebSocketService();
export default wsService;