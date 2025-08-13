import { useState, useEffect } from 'react'
import apiService from './services/api.service.js'
import APP_CONFIG from './config/app.config.js'

function App() {
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [services, setServices] = useState([])
  const [servicesStatus, setServicesStatus] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Load data when component mounts
  useEffect(() => {
    testBackendConnection()
    loadDashboardData()
  }, [])

  const testBackendConnection = async () => {
    try {
      console.log('🔄 Testing backend connection...')
      const result = await apiService.testConnection()
      if (result.success) {
        setConnectionStatus('connected')
        console.log('✅ Backend connected successfully:', result.data)
        setError(null)
      } else {
        setConnectionStatus('failed')
        console.error('❌ Backend connection failed:', result.error)
        setError(`Connection failed: ${result.error}`)
      }
    } catch (err) {
      setConnectionStatus('failed')
      console.error('❌ Connection test error:', err)
      setError(`Connection error: ${err.message}`)
    }
  }

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      console.log('🔄 Loading dashboard data...')
      
      // Load services and their status in parallel
      const [servicesResult, statusResult] = await Promise.all([
        apiService.getServices(),
        apiService.getServicesStatus()
      ])

      // Handle services result
      if (servicesResult.success) {
        setServices(servicesResult.data || [])
        console.log('✅ Services loaded:', servicesResult.data?.length || 0, 'services')
      } else {
        console.error('❌ Failed to load services:', servicesResult.error)
        setError(`Failed to load services: ${servicesResult.error}`)
      }

      // Handle status result
      if (statusResult.success) {
        setServicesStatus(statusResult.data || [])
        console.log('✅ Services status loaded:', statusResult.data?.length || 0, 'statuses')
      } else {
        console.error('❌ Failed to load services status:', statusResult.error)
        // Don't set error for status failure, services might still work
      }

    } catch (err) {
      console.error('❌ Dashboard data loading error:', err)
      setError(`Failed to load dashboard: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const refreshData = () => {
    console.log('🔄 Manual refresh triggered')
    testBackendConnection()
    loadDashboardData()
  }

  const getConnectionStatusDisplay = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          color: 'bg-green-500',
          text: 'Connected',
          animation: 'animate-pulse'
        }
      case 'failed':
        return {
          color: 'bg-red-500',
          text: 'Failed',
          animation: ''
        }
      default:
        return {
          color: 'bg-yellow-500',
          text: 'Connecting...',
          animation: 'animate-pulse'
        }
    }
  }

  const connectionDisplay = getConnectionStatusDisplay()

  // Merge services with their status data
  const servicesWithStatus = services.map(service => {
    const status = servicesStatus.find(s => s.service_id === service.service_id)
    return {
      ...service,
      is_healthy: status?.is_healthy || false,
      response_time: status?.response_time || 0,
      status_code: status?.status_code || 'N/A',
      last_check: status?.last_check || null,
      error_message: status?.error_message || null
    }
  })

  // Calculate summary stats
  const totalServices = servicesWithStatus.length
  const healthyServices = servicesWithStatus.filter(s => s.is_healthy).length
  const unhealthyServices = totalServices - healthyServices
  const avgResponseTime = servicesWithStatus.length > 0 
    ? Math.round(servicesWithStatus.reduce((sum, s) => sum + (s.response_time || 0), 0) / servicesWithStatus.length)
    : 0

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            
            {/* Logo Section */}
            <div className="flex flex-col">
              <div className="text-2xl font-bold">
                <span className="text-cyan-400">Kb</span>
                <span className="text-purple-400">Eye</span>
              </div>
              <div className="text-xs text-gray-400 font-medium uppercase tracking-wide">
                Monitoring Dashboard v{APP_CONFIG.APP.VERSION}
              </div>
            </div>

            {/* System Health Summary - Real Data */}
            <div className="hidden md:flex items-center space-x-8">
              <div className="text-center">
                <div className="text-lg font-semibold text-white">
                  {loading ? '--' : totalServices}
                </div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Services</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-green-400">
                  {loading ? '--' : healthyServices}
                </div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-red-400">
                  {loading ? '--' : unhealthyServices}
                </div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Issues</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-white">
                  {loading ? '--' : avgResponseTime}ms
                </div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Avg Response</div>
              </div>
            </div>

            {/* Header Actions */}
            <div className="flex items-center space-x-4">
              {/* Real Connection Status */}
              <div className="flex items-center space-x-2 px-3 py-2 bg-gray-900 rounded-full border border-gray-700">
                <div className={`w-2 h-2 rounded-full transition-colors duration-300 ${connectionDisplay.color} ${connectionDisplay.animation}`}></div>
                <span className="text-sm font-medium text-gray-300">
                  {connectionDisplay.text}
                </span>
              </div>
              
              {/* Refresh Button */}
              <button 
                onClick={refreshData}
                disabled={loading}
                className="flex items-center space-x-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 font-medium rounded-lg transition-colors duration-200 disabled:opacity-50"
              >
                <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              
              {/* Add Service Button */}
              <button className="flex items-center space-x-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white font-medium rounded-lg transition-colors duration-200">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <span>Add Service</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900 border-l-4 border-red-500 text-red-200 p-4 mx-6 mt-4 rounded">
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">Backend Error:</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Quick Actions Bar */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex space-x-2">
            <button className="px-4 py-2 bg-cyan-500 text-white rounded-lg text-sm font-medium">
              All Services ({totalServices})
            </button>
            <button className="px-4 py-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors">
              Healthy ({healthyServices})
            </button>
            <button className="px-4 py-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors">
              Issues ({unhealthyServices})
            </button>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input 
                type="text" 
                placeholder="Search services..." 
                className="pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        
        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <div className="inline-flex items-center space-x-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
              <span className="text-gray-400">Loading services from backend...</span>
            </div>
          </div>
        )}

        {/* Services Grid - Real Data */}
        {!loading && (
          <>
            {servicesWithStatus.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {servicesWithStatus.map((service, index) => (
                  <div 
                    key={service.id} 
                    className={`bg-gray-800 border-l-4 ${
                      service.is_healthy ? 'border-green-500' : 'border-red-500'
                    } rounded-lg p-6 hover:bg-gray-750 transition-all duration-200 cursor-pointer hover:scale-105 hover:shadow-lg ${
                      service.is_healthy ? 'hover:shadow-green-500/20' : 'hover:shadow-red-500/20'
                    }`}
                    style={{
                      animationDelay: `${index * 0.1}s`
                    }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white truncate">
                        {service.name}
                      </h3>
                      <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${
                        service.is_healthy 
                          ? 'bg-green-900 text-green-400 border-green-800' 
                          : 'bg-red-900 text-red-400 border-red-800'
                      }`}>
                        {service.is_healthy ? 'HEALTHY' : 'DOWN'}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <div className="text-gray-400 uppercase tracking-wide text-xs">Response Time</div>
                        <div className={`font-semibold font-mono ${
                          service.response_time < 200 ? 'text-green-400' : 
                          service.response_time < 1000 ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                          {service.response_time ? Math.round(service.response_time) : 0}ms
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400 uppercase tracking-wide text-xs">Status Code</div>
                        <div className={`font-semibold font-mono ${
                          service.status_code === 200 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {service.status_code}
                        </div>
                      </div>
                    </div>
                    
                    {/* Service URL */}
                    <div className="p-3 bg-gray-900 rounded border border-gray-700 mb-3">
                      <div className="text-xs text-gray-500 font-mono truncate">
                        {service.url}
                      </div>
                    </div>

                    {/* Error Message */}
                    {service.error_message && (
                      <div className="text-xs text-red-400 bg-red-900/20 p-2 rounded border border-red-800">
                        {service.error_message}
                      </div>
                    )}

                    {/* Last Check */}
                    {service.last_check && (
                      <div className="text-xs text-gray-500 mt-2">
                        Last check: {new Date(service.last_check).toLocaleTimeString()}
                      </div>
                    )}

                    {/* Health Pulse Animation */}
                    {service.is_healthy && (
                      <div className="absolute top-4 left-0 w-1 h-8 bg-green-500 rounded-r animate-pulse"></div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              // Empty State
              <div className="text-center py-20">
                <div className="mb-8">
                  <svg className="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <h3 className="text-xl font-semibold text-gray-300 mb-2">No Services Found</h3>
                  <p className="text-gray-500 mb-8">
                    {connectionStatus === 'connected' 
                      ? 'Connected to backend, but no services are configured. Add your first service to start monitoring!'
                      : 'Backend connection failed. Please check if your KbEye backend is running on http://localhost:8000'
                    }
                  </p>
                  <button className="bg-cyan-500 hover:bg-cyan-600 text-white font-medium px-6 py-3 rounded-lg transition-colors duration-200">
                    Add Your First Service
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Debug Info */}
        {connectionStatus === 'connected' && (
          <div className="mt-12 text-center">
            <p className="text-gray-500 text-sm">
              🎉 Successfully connected to KbEye backend at {apiService.getBaseUrl()}
            </p>
            <p className="text-gray-600 text-xs mt-1">
              Backend API working • Services: {totalServices} • Healthy: {healthyServices} • Issues: {unhealthyServices}
            </p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App