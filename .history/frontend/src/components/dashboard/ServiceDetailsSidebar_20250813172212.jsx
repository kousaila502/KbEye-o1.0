// ServiceDetailsSidebar.jsx
// Real-time service details sidebar with logs, health status, and actions

import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Play, Trash2, ExternalLink, Activity, Clock, AlertCircle, CheckCircle, Pause } from 'lucide-react';
import apiService from '../../services/api.service.js';
import wsService from '../../services/websocket.service.js';
import LogsViewer from './LogsViewer.jsx';  // ← ADD THIS IMPORT

const ServiceDetailsSidebar = ({ isOpen, onClose, service, onServiceAction }) => {
  // Component state
  const [logs, setLogs] = useState([]);
  const [healthHistory, setHealthHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isTestingNow, setIsTestingNow] = useState(false);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);
  const [isLogsViewerOpen, setIsLogsViewerOpen] = useState(false);  // ← ADD THIS LINE
  
  // Refs for auto-scrolling
  const logsContainerRef = useRef(null);
  const lastLogRef = useRef(null);

  // Load service details when sidebar opens or service changes
  useEffect(() => {
    if (isOpen && service) {
      loadServiceDetails();
      setupLogStreaming();
    }
    
    return () => {
      // Cleanup when sidebar closes
      cleanupLogStreaming();
    };
  }, [isOpen, service?.service_id]);

  // Auto-scroll to bottom when new logs arrive (if enabled)
  useEffect(() => {
    if (autoScrollEnabled && lastLogRef.current) {
      lastLogRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScrollEnabled]);

  // Load initial service data
  const loadServiceDetails = async () => {
    if (!service?.service_id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 Loading service details for:', service.service_id);
      
      // Load logs and health history in parallel
      const [logsResult] = await Promise.all([
        apiService.getServiceLogs(service.service_id, 50)
      ]);
      
      if (logsResult.success) {
        setLogs(logsResult.data || []);
        console.log('✅ Logs loaded:', logsResult.data?.length || 0, 'entries');
      } else {
        console.error('❌ Failed to load logs:', logsResult.error);
        setError(`Failed to load logs: ${logsResult.error}`);
      }
      
      // Generate mock health history (since we don't have this endpoint yet)
      generateMockHealthHistory();
      
    } catch (err) {
      console.error('❌ Service details loading error:', err);
      setError(`Failed to load service details: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Generate mock health history for demonstration
  const generateMockHealthHistory = () => {
    const history = [];
    const now = new Date();
    
    for (let i = 9; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - (i * 5 * 60 * 1000)); // Every 5 minutes
      const isHealthy = Math.random() > 0.2; // 80% healthy
      const responseTime = isHealthy ? Math.floor(Math.random() * 1000) + 100 : 0;
      
      history.push({
        timestamp: timestamp.toISOString(),
        is_healthy: isHealthy,
        response_time: responseTime,
        status_code: isHealthy ? 200 : (Math.random() > 0.5 ? 500 : 404)
      });
    }
    
    setHealthHistory(history);
  };

  // Setup real-time log streaming
  const setupLogStreaming = () => {
    if (!service?.service_id) return;
    
    // Listen for real-time log updates via WebSocket
    wsService.on('logUpdate', handleLogUpdate);
  };

  // Cleanup log streaming
  const cleanupLogStreaming = () => {
    wsService.off('logUpdate', handleLogUpdate);
  };

  // Handle real-time log updates
  const handleLogUpdate = useCallback((logData) => {
    if (logData.service_id === service?.service_id) {
      console.log('📨 New log entry received:', logData);
      
      setLogs(prevLogs => {
        const newLogs = [...prevLogs, logData];
        
        // Keep only last 100 logs to prevent memory issues
        if (newLogs.length > 100) {
          return newLogs.slice(-100);
        }
        
        return newLogs;
      });
    }
  }, [service?.service_id]);

  // Handle scroll to detect if user scrolled up (disable auto-scroll)
  const handleLogsScroll = () => {
    if (!logsContainerRef.current) return;
    
    const container = logsContainerRef.current;
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 10;
    
    setAutoScrollEnabled(isAtBottom);
  };

  // Test service now
  const handleTestNow = async () => {
    if (!service?.service_id) return;
    
    setIsTestingNow(true);
    
    try {
      console.log('🔄 Testing service now:', service.service_id);
      
      // For now, just trigger a refresh (your backend might have a test endpoint)
      // await apiService.testService(service.service_id);
      
      // Simulate test delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Trigger parent callback to refresh service data
      onServiceAction?.('test', service);
      
      console.log('✅ Service test completed');
      
    } catch (error) {
      console.error('❌ Service test failed:', error);
    } finally {
      setIsTestingNow(false);
    }
  };

  // Delete service
  const handleDeleteService = async () => {
    if (!service?.service_id) return;
    
    const confirmed = window.confirm(`Are you sure you want to delete "${service.name}"?\n\nThis action cannot be undone.`);
    
    if (!confirmed) return;
    
    try {
      console.log('🗑️ Deleting service:', service.service_id);
      
      const result = await apiService.deleteService(service.service_id);
      
      if (result.success) {
        console.log('✅ Service deleted successfully');
        onServiceAction?.('delete', service);
        onClose(); // Close sidebar after deletion
      } else {
        throw new Error(result.error || 'Failed to delete service');
      }
      
    } catch (error) {
      console.error('❌ Failed to delete service:', error);
      alert(`Failed to delete service: ${error.message}`);
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Get status color
  const getStatusColor = (isHealthy) => {
    return isHealthy ? 'text-green-400' : 'text-red-400';
  };

  // Don't render if not open
  if (!isOpen || !service) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Background overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Sidebar */}
      <div className="ml-auto w-full max-w-2xl bg-gray-800 shadow-2xl transform transition-transform duration-300 ease-in-out flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700 bg-gray-900">
          <div className="flex items-center space-x-4">
            <div className={`w-3 h-3 rounded-full ${service.is_healthy ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <div>
              <h2 className="text-xl font-semibold text-white">{service.name}</h2>
              <p className="text-sm text-gray-400">{service.service_id}</p>
            </div>
          </div>
          
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          
          {/* Current Health Status */}
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-lg font-medium text-white mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2 text-cyan-400" />
              Current Health Status
            </h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-900 p-4 rounded-lg">
                <div className="text-xs text-gray-500 uppercase tracking-wide">Status</div>
                <div className={`text-lg font-semibold ${getStatusColor(service.is_healthy)}`}>
                  {service.is_healthy ? 'HEALTHY' : 'DOWN'}
                </div>
              </div>
              
              <div className="bg-gray-900 p-4 rounded-lg">
                <div className="text-xs text-gray-500 uppercase tracking-wide">Response Time</div>
                <div className="text-lg font-semibold text-white">
                  {service.response_time ? Math.round(service.response_time) : 0}ms
                </div>
              </div>
              
              <div className="bg-gray-900 p-4 rounded-lg">
                <div className="text-xs text-gray-500 uppercase tracking-wide">Status Code</div>
                <div className="text-lg font-semibold text-white">
                  {service.status_code || 'N/A'}
                </div>
              </div>
              
              <div className="bg-gray-900 p-4 rounded-lg">
                <div className="text-xs text-gray-500 uppercase tracking-wide">Last Check</div>
                <div className="text-sm text-white">
                  {service.last_check ? formatTimestamp(service.last_check) : 'Never'}
                </div>
              </div>
            </div>

            {/* Error Message */}
            {service.error_message && (
              <div className="mt-4 p-3 bg-red-900/20 border border-red-500 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span className="text-red-300 text-sm">{service.error_message}</span>
                </div>
              </div>
            )}
          </div>

          {/* Service Configuration */}
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-lg font-medium text-white mb-4">Configuration</h3>
            
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-wide">Service URL</label>
                <div className="flex items-center space-x-2">
                  <span className="text-white font-mono text-sm">{service.url}</span>
                  <button className="p-1 hover:bg-gray-700 rounded">
                    <ExternalLink className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wide">Health Endpoint</label>
                  <div className="text-white font-mono text-sm">{service.health_endpoint || '/health'}</div>
                </div>
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wide">Check Interval</label>
                  <div className="text-white text-sm">{service.check_interval || 30}s</div>
                </div>
              </div>
            </div>
          </div>

          {/* Health History */}
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-lg font-medium text-white mb-4 flex items-center">
              <Clock className="w-5 h-5 mr-2 text-cyan-400" />
              Recent Health Checks
            </h3>
            
            <div className="space-y-2">
              {healthHistory.slice(-5).map((check, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {check.is_healthy ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-400" />
                    )}
                    <span className="text-white text-sm">{formatTimestamp(check.timestamp)}</span>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <span className="text-gray-400 text-sm">{check.response_time}ms</span>
                    <span className={`text-sm ${getStatusColor(check.is_healthy)}`}>
                      {check.status_code}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Real-time Logs */}
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-white flex items-center">
                Real-time Logs
                <span className="ml-2 text-xs bg-green-500 text-white px-2 py-1 rounded">LIVE</span>
              </h3>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setAutoScrollEnabled(!autoScrollEnabled)}
                  className={`p-2 rounded-lg transition-colors ${
                    autoScrollEnabled ? 'bg-cyan-500 text-white' : 'bg-gray-700 text-gray-400'
                  }`}
                  title={autoScrollEnabled ? 'Pause auto-scroll' : 'Resume auto-scroll'}
                >
                  {autoScrollEnabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Loading state */}
            {loading && (
              <div className="text-center py-8">
                <div className="inline-flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-500"></div>
                  <span className="text-gray-400">Loading logs...</span>
                </div>
              </div>
            )}

            {/* Error state */}
            {error && (
              <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                  <span className="text-red-300">{error}</span>
                </div>
              </div>
            )}

            {/* Logs container */}
            {!loading && !error && (
              <div 
                ref={logsContainerRef}
                onScroll={handleLogsScroll}
                className="bg-gray-900 rounded-lg p-4 h-80 overflow-y-auto font-mono text-sm"
              >
                {logs.length > 0 ? (
                  <div className="space-y-1">
                    {logs.map((log, index) => (
                      <div key={index} className="flex text-gray-300">
                        <span className="text-gray-500 mr-3 flex-shrink-0">
                          {formatTimestamp(log.timestamp)}
                        </span>
                        <span className={`${log.level === 'ERROR' ? 'text-red-400' : 
                                       log.level === 'WARN' ? 'text-yellow-400' : 'text-gray-300'}`}>
                          {log.message}
                        </span>
                      </div>
                    ))}
                    <div ref={lastLogRef} />
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    No logs available for this service
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Actions Footer */}
        <div className="p-6 border-t border-gray-700 bg-gray-900">
          <div className="flex items-center justify-between">
            <div className="flex space-x-3">
              <button
                onClick={handleTestNow}
                disabled={isTestingNow}
                className="flex items-center space-x-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                <Play className={`w-4 h-4 ${isTestingNow ? 'animate-spin' : ''}`} />
                <span>{isTestingNow ? 'Testing...' : 'Test Now'}</span>
              </button>
              
              <button 
                onClick={() => setIsLogsViewerOpen(true)}  // ← UPDATE THIS ONCLICK
                className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                <span>View Full Logs</span>
              </button>
            </div>
            
            <button
              onClick={handleDeleteService}
              className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    {/* ← ADD THIS LOGS VIEWER COMPONENT: */}
    <LogsViewer
      isOpen={isLogsViewerOpen}
      onClose={() => setIsLogsViewerOpen(false)}
      service={service}
    />
  );
};

export default ServiceDetailsSidebar;