import { useState, useEffect } from 'react'
import apiService from './services/api.service.js'
import APP_CONFIG from './config/app.config.js'

function App() {
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [services, setServices] = useState([])
  const [servicesStatus, setServicesStatus] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Test backend connection on component mount
  useEffect(() => {
    testBackendConnection()
    loadDashboardData()
  }, [])

  const testBackendConnection = async () => {
    try {
      const result = await apiService.testConnection()
      if (result.success) {
        setConnectionStatus('connected')
        console.log('✅ Backend connection successful:', result.data)
      } else {
        setConnectionStatus('failed')
        console.error('❌ Backend connection failed:', result.error)
      }
    } catch (err) {
      setConnectionStatus('failed')
      console.error('❌ Connection test error:', err)
    }
  }

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      // Load services and their status
      const [servicesResult, statusResult] = await Promise.all([
        apiService.getServices(),
        apiService.getServicesStatus()
      ])

      if (servicesResult.success) {
        setServices(servicesResult.data)
        console.log('✅ Services loaded:', servicesResult.data)
      } else {
        console.error('❌ Failed to load services:', servicesResult.error)
        setError('Failed to load services')
      }

      if (statusResult.success) {
        setServicesStatus(statusResult.data)
        console.log('✅ Services status loaded:', statusResult.data)
      } else {
        console.error('❌ Failed to load services status:', statusResult.error)
      }

    } catch (err) {
      console.error('❌ Dashboard data loading error:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const getConnectionStatusDisplay = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          color: 'bg-success-500',
          text: 'Connected',
          animation: 'animate-pulse'
        }
      case 'failed':
        return {
          color: 'bg-danger-500',
          text: 'Connection Failed',
          animation: ''
        }
      default:
        return {
          color: 'bg-warning-500',
          text: 'Connecting...',
          animation: 'animate-pulse'
        }
    }
  }

  const connectionDisplay = getConnectionStatusDisplay()

  // Calculate summary stats
  const totalServices = services.length
  const healthyServices = servicesStatus.filter(s => s.is_healthy).length
  const unhealthyServices = totalServices - healthyServices
  const avgResponseTime = servicesStatus.length > 0 
    ? Math.round(servicesStatus.reduce((sum, s) => sum + (s.response_time || 0), 0) / servicesStatus.length)
    : 0

  return (
    <div className="min-h-screen bg-gray-850">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            
            {/* Logo Section */}
            <div className="flex flex-col">
              <div className="text-2xl font-bold">
                <span className="text-primary-500">Kb</span>
                <span className="text-purple-500">Eye</span>
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
                <div className="text-lg font-semibold text-success-500">
                  {loading ? '--' : healthyServices}
                </div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-danger-500">
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
                onClick={loadDashboardData}
                disabled={loading}
                className="flex items-center space-x-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 font-medium rounded-lg transition-colors duration-200 disabled:opacity-50"
              >
                <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              
              {/* Add Service Button */}
              <button className="flex items-center space-x-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white font-medium rounded-lg transition-colors duration-200">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <span>Add Service</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        
        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-danger-900 border border-danger-700 text-danger-200 px-4 py-3 rounded-lg">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <div className="inline-flex items-center space-x-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
              <span className="text-gray-400">Loading services...</span>
            </div>
          </div>
        )}

        {/* Services Grid - Real Data */}
        {!loading && (
          <>
            {services.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {services.map((service) => {
                  // Find matching status for this service
                  const status = servicesStatus.find(s => s.service_id === service.service_id)
                  const isHealthy = status?.is_healthy || false
                  const responseTime = status?.response_time || 0
                  const statusCode = status?.status_code || 'Unknown'
                  
                  return (
                    <div 
                      key={service.id} 
                      className={`bg-gray-800 border-l-4 ${
                        isHealthy ? 'border-success-500' : 'border-danger-500'
                      } rounded-lg p-6 hover:bg-gray-750 transition-all duration-200 cursor-pointer hover:scale-105`}
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-white truncate">
                          {service.name}
                        </h3>
                        <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${
                          isHealthy 
                            ? 'bg-success-900 text-success-400 border-success-800' 
                            : 'bg-danger-900 text-danger-400 border-danger-800'
                        }`}>
                          {isHealthy ? 'HEALTHY' : 'DOWN'}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                        <div>
                          <div className="text-gray-400 uppercase tracking-wide text-xs">Response Time</div>
                          <div className="text-white font-semibold font-mono">
                            {Math.round(responseTime)}ms
                          </div>
                        </div>
                        <div>
                          <div className="text-gray-400 uppercase tracking-wide text-xs">Status Code</div>
                          <div className="text-white font-semibold font-mono">{statusCode}</div>
                        </div>
                      </div>
                      
                      <div className="p-3 bg-gray-900 rounded border border-gray-700">
                        <div className="text-xs text-gray-500 font-mono truncate">
                          {service.url}
                        </div>
                      </div>
                    </div>
                  )
                })}
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
                    Start monitoring your microservices by adding your first service.
                  </p>
                  <button className="bg-primary-500 hover:bg-primary-600 text-white font-medium px-6 py-3 rounded-lg transition-colors duration-200">
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
              🚀 Successfully connected to KbEye backend at {apiService.getBaseUrl()}
            </p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App