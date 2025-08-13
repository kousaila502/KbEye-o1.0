import { useState, useEffect } from 'react'

function App() {
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Simulate connection after 1 second
    const timer = setTimeout(() => setIsConnected(true), 1000)
    return () => clearTimeout(timer)
  }, [])

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
                Monitoring Dashboard
              </div>
            </div>

            {/* System Health Summary */}
            <div className="hidden md:flex items-center space-x-8">
              <div className="text-center">
                <div className="text-lg font-semibold text-white">--</div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Services</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-success-500">--</div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-danger-500">--</div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Issues</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-white">--ms</div>
                <div className="text-xs text-gray-400 uppercase tracking-wide">Avg Response</div>
              </div>
            </div>

            {/* Header Actions */}
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2 px-3 py-2 bg-gray-900 rounded-full border border-gray-700">
                <div className={`w-2 h-2 rounded-full transition-colors duration-300 ${
                  isConnected 
                    ? 'bg-success-500 animate-pulse' 
                    : 'bg-danger-500'
                }`}></div>
                <span className="text-sm font-medium text-gray-300">
                  {isConnected ? 'Connected' : 'Connecting...'}
                </span>
              </div>
              
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
        <div className="text-center py-20">
          <div className="mb-8">
            <div className="text-6xl font-bold mb-4">
              <span className="text-primary-500">Kb</span>
              <span className="text-purple-500">Eye</span>
            </div>
            <p className="text-xl text-gray-400 mb-8">
              Professional Microservices Monitoring Dashboard
            </p>
          </div>
          
          {/* Status Cards Preview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {/* Sample Service Cards */}
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:bg-gray-750 transition-colors duration-200">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Service {i}</h3>
                  <span className="px-3 py-1 bg-success-900 text-success-400 text-xs font-semibold rounded-full border border-success-800">
                    HEALTHY
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-400 uppercase tracking-wide text-xs">Response Time</div>
                    <div className="text-white font-semibold font-mono">123ms</div>
                  </div>
                  <div>
                    <div className="text-gray-400 uppercase tracking-wide text-xs">Status Code</div>
                    <div className="text-white font-semibold font-mono">200</div>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-gray-900 rounded border border-gray-700">
                  <div className="text-xs text-gray-500 font-mono truncate">
                    https://api.example{i}.com
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12">
            <p className="text-gray-500">
              🚀 React + Vite + Tailwind setup complete! Ready to build components.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App