import { useState, useEffect } from 'react'
import APP_CONFIG from './config/app.config.js'

function App() {
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(false)

  // Simulate connection and sample data
  useEffect(() => {
    // Simulate connection after 1 second
    const timer = setTimeout(() => {
      setConnectionStatus('connected')
      // Add some sample services for demo
      setSampleServices()
    }, 1000)
    return () => clearTimeout(timer)
  }, [])

  const setSampleServices = () => {
    const sampleServices = [
      {
        id: 1,
        service_id: 'user-api',
        name: 'User API Service',
        url: 'https://api.users.example.com',
        is_healthy: true,
        response_time: 145.2,
        status_code: 200,
        last_check: new Date().toISOString()
      },
      {
        id: 2,
        service_id: 'payment-api',
        name: 'Payment Processing',
        url: 'https://payments.example.com',
        is_healthy: false,
        response_time: 8924.1,
        status_code: 502,
        last_check: new Date().toISOString()
      },
      {
        id: 3,
        service_id: 'notification-service',
        name: 'Notification Service',
        url: 'https://notifications.example.com',
        is_healthy: true,
        response_time: 67.8,
        status_code: 200,
        last_check: new Date().toISOString()
      },
      {
        id: 4,
        service_id: 'analytics-api',
        name: 'Analytics Engine',
        url: 'https://analytics.example.com',
        is_healthy: true,
        response_time: 234.5,
        status_code: 200,
        last_check: new Date().toISOString()
      }
    ]
    setServices(sampleServices)
  }

  const refreshData = () => {
    setLoading(true)
    // Simulate loading
    setTimeout(() => {
      setSampleServices()
      setLoading(false)
    }, 1000)
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
          text: 'Connection Failed',
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

  // Calculate summary stats
  const totalServices = services.length
  const healthyServices = services.filter(s => s.is_healthy).length
  const unhealthyServices = totalServices - healthyServices
  const avgResponseTime = services.length > 0 
    ? Math.round(services.reduce((sum, s) => sum + (s.response_time || 0), 0) / services.length)
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

            {/* System Health Summary */}
            <div className="hidden md:flex items-center space-x-8">
              <div className="text-center">
                <div className="text-lg font-semibold text-white">{totalServices}</div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Services</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-green-400">{healthyServices}</div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-red-400">{unhealthyServices}</div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Issues</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-white">{avgResponseTime}ms</div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Avg Response</div>
              </div>
            </div>

            {/* Header Actions */}
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
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

      {/* Quick Actions Bar */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex space-x-2">
            <button className="px-4 py-2 bg-cyan-500 text-white rounded-lg text-sm font-medium">
              All Services
            </button>
            <button className="px-4 py-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors">
              Healthy
            </button>
            <button className="px-4 py-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors">
              Issues
            </button>
            <button className="px-4 py-2 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors">
              Unknown
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
            <button className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>View Logs</span>
            </button>
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
              <span className="text-gray-400">Refreshing services...</span>
            </div>
          </div>
        )}

        {/* Services Grid */}
        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {services.map((service, index) => (
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
                      {Math.round(service.response_time)}ms
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
                
                <div className="p-3 bg-gray-900 rounded border border-gray-700">
                  <div className="text-xs text-gray-500 font-mono truncate">
                    {service.url}
                  </div>
                </div>

                {service.is_healthy && (
                  <div className="absolute top-4 left-0 w-1 h-8 bg-green-500 rounded-r animate-pulse"></div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Success Message */}
        <div className="mt-12 text-center">
          <p className="text-gray-500 text-sm">
            🎉 KbEye Professional Dashboard - React + Vite + Tailwind Setup Complete!
          </p>
        </div>
      </main>
    </div>
  )
}

export default App