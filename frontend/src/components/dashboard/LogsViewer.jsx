// LogsViewer.jsx
// Full-screen logs viewer with advanced filtering, search, and real-time streaming

import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  X, Search, Filter, Download, Play, Pause, RefreshCw, 
  AlertCircle, Info, AlertTriangle, Calendar, Clock,
  ChevronDown, ChevronUp, Copy, Maximize2, Minimize2
} from 'lucide-react';
import apiService from '../../services/api.service.js';
import wsService from '../../services/websocket.service.js';

const LogsViewer = ({ isOpen, onClose, service }) => {
  // Component state
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isStreaming, setIsStreaming] = useState(true);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);
  
  // Filter and search state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('ALL');
  const [timeRange, setTimeRange] = useState('1h'); // 1h, 6h, 24h, all
  const [showFilters, setShowFilters] = useState(false);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [logsPerPage] = useState(100);
  const [totalLogs, setTotalLogs] = useState(0);
  
  // UI state
  const [viewMode, setViewMode] = useState('formatted'); // formatted, raw, table
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);
  
  // Refs
  const logsContainerRef = useRef(null);
  const lastLogRef = useRef(null);
  const searchInputRef = useRef(null);

  // Load logs when viewer opens or filters change
  useEffect(() => {
    if (isOpen && service) {
      loadLogs();
      if (isStreaming) {
        setupLogStreaming();
      }
    }
    
    return () => {
      cleanupLogStreaming();
    };
  }, [isOpen, service?.service_id, currentPage, timeRange]);

  // Filter logs when search or level filter changes
  useEffect(() => {
    filterLogs();
  }, [logs, searchQuery, selectedLevel]);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScrollEnabled && lastLogRef.current && filteredLogs.length > 0) {
      lastLogRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs, autoScrollEnabled]);

  // Load logs from backend
  const loadLogs = async () => {
    if (!service?.service_id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 Loading logs for:', service.service_id);
      
      // Calculate lines to fetch based on page and filters
      const linesToFetch = currentPage * logsPerPage;
      
      const result = await apiService.getServiceLogs(service.service_id, linesToFetch);
      
      if (result.success) {
        const logsData = result.data || [];
        setLogs(logsData);
        setTotalLogs(logsData.length);
        console.log('✅ Logs loaded:', logsData.length, 'entries');
      } else {
        console.warn('⚠️ Failed to load logs:', result.error);
        setError(`Failed to load logs: ${result.error}`);
        setLogs([]);
      }
      
    } catch (err) {
      console.error('❌ Logs loading error:', err);
      setError(`Failed to load logs: ${err.message}`);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  // Setup real-time log streaming
  const setupLogStreaming = () => {
    if (!service?.service_id || !isStreaming) return;
    
    console.log('🔄 Setting up log streaming for:', service.service_id);
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
        // Ensure prevLogs is always an array
        const logsArray = Array.isArray(prevLogs) ? prevLogs : [];
        const newLogs = [...logsArray, logData];
        
        // Keep only last 1000 logs to prevent memory issues
        if (newLogs.length > 1000) {
          return newLogs.slice(-1000);
        }
        
        return newLogs;
      });
    }
  }, [service?.service_id]);

  // Filter logs based on search and level
  const filterLogs = () => {
    // Ensure logs is always an array
    const logsArray = Array.isArray(logs) ? logs : [];
    let filtered = [...logsArray];
    
    // Filter by log level
    if (selectedLevel !== 'ALL') {
      filtered = filtered.filter(log => log.level === selectedLevel);
    }
    
    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(query) ||
        log.level.toLowerCase().includes(query)
      );
    }
    
    // Filter by time range
    if (timeRange !== 'all') {
      const now = new Date();
      const hours = timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : 24;
      const cutoff = new Date(now.getTime() - (hours * 60 * 60 * 1000));
      
      filtered = filtered.filter(log => new Date(log.timestamp) >= cutoff);
    }
    
    setFilteredLogs(filtered);
  };

  // Handle scroll to detect if user scrolled up
  const handleLogsScroll = () => {
    if (!logsContainerRef.current) return;
    
    const container = logsContainerRef.current;
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;
    
    setAutoScrollEnabled(isAtBottom);
  };

  // Toggle streaming
  const toggleStreaming = () => {
    const newStreaming = !isStreaming;
    setIsStreaming(newStreaming);
    
    if (newStreaming) {
      setupLogStreaming();
    } else {
      cleanupLogStreaming();
    }
  };

  // Refresh logs
  const refreshLogs = () => {
    setCurrentPage(1);
    loadLogs();
  };

  // Export logs
  const exportLogs = () => {
    const dataToExport = filteredLogs.map(log => ({
      timestamp: log.timestamp,
      level: log.level,
      message: log.message,
      service_id: log.service_id
    }));
    
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${service.service_id}-logs-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('✅ Logs exported:', filteredLogs.length, 'entries');
  };

  // Copy log to clipboard
  const copyLogToClipboard = (log) => {
    const logText = `[${log.timestamp}] ${log.level}: ${log.message}`;
    navigator.clipboard.writeText(logText);
    console.log('✅ Log copied to clipboard');
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString(),
      full: date.toLocaleString()
    };
  };

  // Get log level color and icon
  const getLogLevelStyle = (level) => {
    switch (level) {
      case 'ERROR':
        return { 
          color: 'text-red-400', 
          bg: 'bg-red-900/20', 
          border: 'border-red-500/30',
          icon: AlertCircle 
        };
      case 'WARN':
        return { 
          color: 'text-yellow-400', 
          bg: 'bg-yellow-900/20', 
          border: 'border-yellow-500/30',
          icon: AlertTriangle 
        };
      case 'INFO':
        return { 
          color: 'text-blue-400', 
          bg: 'bg-blue-900/20', 
          border: 'border-blue-500/30',
          icon: Info 
        };
      default:
        return { 
          color: 'text-gray-400', 
          bg: 'bg-gray-900/20', 
          border: 'border-gray-500/30',
          icon: Info 
        };
    }
  };

  // Don't render if not open
  if (!isOpen || !service) return null;

  const logLevels = ['ALL', 'ERROR', 'WARN', 'INFO'];
  const timeRanges = [
    { value: '1h', label: 'Last Hour' },
    { value: '6h', label: 'Last 6 Hours' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: 'all', label: 'All Time' }
  ];

  return (
    <div className="fixed inset-0 z-50 bg-gray-900">
      
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${service.is_healthy ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <div>
              <h1 className="text-xl font-semibold text-white">Logs Viewer</h1>
              <p className="text-sm text-gray-400">{service.name} ({service.service_id})</p>
            </div>
          </div>
          
          {/* Real-time indicator */}
          <div className="flex items-center space-x-2">
            {isStreaming && (
              <span className="flex items-center space-x-1 text-xs bg-green-500 text-white px-2 py-1 rounded">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                <span>LIVE</span>
              </span>
            )}
            <span className="text-sm text-gray-400">
              {filteredLogs.length} of {totalLogs} logs
            </span>
          </div>
        </div>

        {/* Header actions */}
        <div className="flex items-center space-x-2">
          {/* Back to Dashboard button */}
          <button
            onClick={onClose}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded-lg transition-colors"
            title="Back to Service Details"
          >
            <X className="w-4 h-4" />
            <span className="hidden sm:inline">Back</span>
          </button>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 w-64"
            />
          </div>

          {/* Filters toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition-colors ${
              showFilters ? 'bg-cyan-500 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <Filter className="w-4 h-4" />
          </button>

          {/* Actions */}
          <button
            onClick={toggleStreaming}
            className={`p-2 rounded-lg transition-colors ${
              isStreaming ? 'bg-red-500 text-white' : 'bg-green-500 text-white'
            }`}
            title={isStreaming ? 'Stop streaming' : 'Start streaming'}
          >
            {isStreaming ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          <button
            onClick={refreshLogs}
            disabled={loading}
            className="p-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
            title="Refresh logs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={exportLogs}
            className="p-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded-lg transition-colors"
            title="Export logs"
          >
            <Download className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded-lg transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          <button
            onClick={onClose}
            className="p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            title="Close Logs Viewer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="p-4 border-b border-gray-700 bg-gray-800">
          <div className="flex items-center space-x-6">
            {/* Log level filter */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-400">Level:</span>
              <select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                {logLevels.map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
            </div>

            {/* Time range filter */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-400">Time:</span>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                {timeRanges.map(range => (
                  <option key={range.value} value={range.value}>{range.label}</option>
                ))}
              </select>
            </div>

            {/* View mode */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-400">View:</span>
              <select
                value={viewMode}
                onChange={(e) => setViewMode(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                <option value="formatted">Formatted</option>
                <option value="raw">Raw</option>
                <option value="table">Table</option>
              </select>
            </div>

            {/* Auto-scroll toggle */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoScroll"
                checked={autoScrollEnabled}
                onChange={(e) => setAutoScrollEnabled(e.target.checked)}
                className="w-4 h-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
              />
              <label htmlFor="autoScroll" className="text-sm text-gray-400">Auto-scroll</label>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        
        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
              <span className="text-gray-400">Loading logs...</span>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <div className="flex items-center justify-center h-full">
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-6 max-w-md">
              <div className="flex items-center space-x-3">
                <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
                <div>
                  <h3 className="text-red-300 font-medium">Failed to load logs</h3>
                  <p className="text-red-400 text-sm mt-1">{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Logs display */}
        {!loading && !error && (
          <div 
            ref={logsContainerRef}
            onScroll={handleLogsScroll}
            className="h-full overflow-y-auto p-4"
          >
            {filteredLogs.length > 0 ? (
              <div className="space-y-1">
                {filteredLogs.map((log, index) => {
                  const style = getLogLevelStyle(log.level);
                  const timestamp = formatTimestamp(log.timestamp);
                  const IconComponent = style.icon;
                  
                  return (
                    <div
                      key={index}
                      className={`group relative p-3 rounded border transition-colors hover:bg-gray-800 ${style.bg} ${style.border}`}
                      onClick={() => setSelectedLog(selectedLog === index ? null : index)}
                    >
                      {viewMode === 'formatted' ? (
                        <div className="flex items-start space-x-3">
                          <IconComponent className={`w-4 h-4 mt-0.5 flex-shrink-0 ${style.color}`} />
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-3 mb-1">
                              <span className={`font-medium text-xs px-2 py-0.5 rounded ${style.color}`}>
                                {log.level}
                              </span>
                              <span className="text-xs text-gray-500" title={timestamp.full}>
                                {timestamp.time}
                              </span>
                            </div>
                            
                            <div className="text-gray-300 text-sm font-mono leading-relaxed">
                              {log.message}
                            </div>
                          </div>
                          
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              copyLogToClipboard(log);
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-white transition-opacity"
                            title="Copy to clipboard"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                      ) : viewMode === 'raw' ? (
                        <div className="font-mono text-sm text-gray-300">
                          [{timestamp.full}] {log.level}: {log.message}
                        </div>
                      ) : (
                        <div className="grid grid-cols-4 gap-4 text-sm">
                          <div className="text-gray-500">{timestamp.time}</div>
                          <div className={style.color}>{log.level}</div>
                          <div className="col-span-2 text-gray-300 font-mono">{log.message}</div>
                        </div>
                      )}
                    </div>
                  );
                })}
                <div ref={lastLogRef} />
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-6xl mb-4">📋</div>
                  <h3 className="text-xl text-gray-300 mb-2">No logs found</h3>
                  <p className="text-gray-500">
                    {searchQuery || selectedLevel !== 'ALL' ? 
                      'Try adjusting your search or filters' : 
                      'No logs available for this service'
                    }
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LogsViewer;