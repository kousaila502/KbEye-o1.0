// AddServiceModal.jsx
// Modal component for adding new services to KbEye monitoring

import { useState, useEffect } from 'react';
import { X, Plus, AlertCircle, CheckCircle } from 'lucide-react';

const AddServiceModal = ({ isOpen, onClose, onServiceAdded, existingServices = [] }) => {
  // Form state
  const [formData, setFormData] = useState({
    service_id: '',
    name: '',
    url: '',
    health_endpoint: '/health',
    logs_endpoint: '/logs',
    check_interval: 30,
    log_lines: 50,
    timeout: 5000,
    expected_status: 200
  });

  // UI state
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setFormData({
        service_id: '',
        name: '',
        url: '',
        health_endpoint: '/health',
        logs_endpoint: '/logs',
        check_interval: 30,
        log_lines: 50,
        timeout: 5000,
        expected_status: 200
      });
      setErrors({});
      setTouched({});
    }
  }, [isOpen]);

  // Validation rules
  const validateField = (name, value) => {
    switch (name) {
      case 'service_id':
        if (!value.trim()) return 'Service ID is required';
        if (!/^[a-zA-Z0-9-_]+$/.test(value)) return 'Service ID can only contain letters, numbers, hyphens, and underscores';
        if (existingServices.some(s => s.service_id === value)) return 'Service ID already exists';
        return '';

      case 'name':
        if (!value.trim()) return 'Service name is required';
        if (value.length < 3) return 'Service name must be at least 3 characters';
        return '';

      case 'url':
        if (!value.trim()) return 'URL is required';
        try {
          const url = new URL(value);
          if (!['http:', 'https:'].includes(url.protocol)) return 'URL must use HTTP or HTTPS';
          return '';
        } catch {
          return 'Please enter a valid URL';
        }

      case 'health_endpoint':
        if (!value.startsWith('/')) return 'Endpoint must start with /';
        return '';

      case 'logs_endpoint':
        if (!value.startsWith('/')) return 'Endpoint must start with /';
        return '';

      case 'check_interval':
        const interval = parseInt(value);
        if (isNaN(interval) || interval < 1) return 'Check interval must be at least 1 second';
        if (interval > 3600) return 'Check interval cannot exceed 1 hour (3600 seconds)';
        return '';

      case 'timeout':
        const timeout = parseInt(value);
        if (isNaN(timeout) || timeout < 1000) return 'Timeout must be at least 1000ms';
        if (timeout > 60000) return 'Timeout cannot exceed 60 seconds';
        return '';

      case 'log_lines':
        const lines = parseInt(value);
        if (isNaN(lines) || lines < 1) return 'Log lines must be at least 1';
        if (lines > 1000) return 'Log lines cannot exceed 1000';
        return '';

      case 'expected_status':
        const status = parseInt(value);
        if (isNaN(status) || status < 100 || status > 599) return 'Status code must be between 100-599';
        return '';

      default:
        return '';
    }
  };

  // Handle input changes (less aggressive validation)
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Update form data
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Mark field as touched
    setTouched(prev => ({
      ...prev,
      [name]: true
    }));

    // Only show validation errors for touched fields that have content
    if (touched[name] && value.trim()) {
      const error = validateField(name, value);
      setErrors(prev => ({
        ...prev,
        [name]: error
      }));
    } else {
      // Clear errors for empty fields
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  // Auto-generate service_id from name
  const handleNameChange = (e) => {
    const name = e.target.value;
    handleInputChange(e);

    // Auto-generate service_id if it's empty
    if (!formData.service_id && name) {
      const generatedId = name
        .toLowerCase()
        .replace(/[^a-zA-Z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .slice(0, 30);
      
      setFormData(prev => ({
        ...prev,
        service_id: generatedId
      }));
      
      // Validate generated ID
      const idError = validateField('service_id', generatedId);
      setErrors(prev => ({
        ...prev,
        service_id: idError
      }));
    }
  };

  // Validate entire form (only for submission)
  const validateForm = () => {
    const newErrors = {};
    
    // Only validate required fields that have been touched or are empty
    if (!formData.name.trim()) newErrors.name = 'Service name is required';
    if (!formData.service_id.trim()) newErrors.service_id = 'Service ID is required';
    if (!formData.url.trim()) newErrors.url = 'URL is required';
    
    // Validate format only if fields have content
    if (formData.name.trim()) {
      const nameError = validateField('name', formData.name);
      if (nameError) newErrors.name = nameError;
    }
    
    if (formData.service_id.trim()) {
      const idError = validateField('service_id', formData.service_id);
      if (idError) newErrors.service_id = idError;
    }
    
    if (formData.url.trim()) {
      const urlError = validateField('url', formData.url);
      if (urlError) newErrors.url = urlError;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    
    try {
      // Call the parent callback with form data
      await onServiceAdded(formData);
      
      // Close modal on success
      onClose();
      
    } catch (error) {
      // Handle API errors
      console.error('Failed to add service:', error);
      setErrors({
        submit: error.message || 'Failed to add service. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  // Don't render if modal is closed
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-cyan-500 rounded-lg flex items-center justify-center">
              <Plus className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Add New Service</h2>
              <p className="text-sm text-gray-400">Monitor a new service endpoint</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            disabled={loading}
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          
          {/* Submit Error */}
          {errors.submit && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <span className="text-red-300">{errors.submit}</span>
            </div>
          )}

          {/* Required Fields Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">
              Required Information
            </h3>
            
            {/* Service Name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Service Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleNameChange}
                className={`w-full px-4 py-3 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-colors ${
                  errors.name ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:ring-cyan-500'
                }`}
                placeholder="e.g., User API, Payment Service"
                disabled={loading}
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-400">{errors.name}</p>
              )}
            </div>

            {/* Service ID */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Service ID *
              </label>
              <input
                type="text"
                name="service_id"
                value={formData.service_id}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-colors ${
                  errors.service_id ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:ring-cyan-500'
                }`}
                placeholder="e.g., user-api, payment-service"
                disabled={loading}
              />
              {errors.service_id && (
                <p className="mt-1 text-sm text-red-400">{errors.service_id}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Unique identifier (letters, numbers, hyphens, underscores only)
              </p>
            </div>

            {/* Service URL */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Service URL *
              </label>
              <input
                type="url"
                name="url"
                value={formData.url}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-colors ${
                  errors.url ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:ring-cyan-500'
                }`}
                placeholder="https://api.example.com"
                disabled={loading}
              />
              {errors.url && (
                <p className="mt-1 text-sm text-red-400">{errors.url}</p>
              )}
            </div>
          </div>

          {/* Optional Configuration Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">
              Optional Configuration
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Health Endpoint */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Health Endpoint
                </label>
                <input
                  type="text"
                  name="health_endpoint"
                  value={formData.health_endpoint}
                  onChange={handleInputChange}
                  className={`w-full px-4 py-3 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-colors ${
                    errors.health_endpoint ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:ring-cyan-500'
                  }`}
                  placeholder="/health"
                  disabled={loading}
                />
                {errors.health_endpoint && (
                  <p className="mt-1 text-sm text-red-400">{errors.health_endpoint}</p>
                )}
              </div>

              {/* Logs Endpoint */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Logs Endpoint
                </label>
                <input
                  type="text"
                  name="logs_endpoint"
                  value={formData.logs_endpoint}
                  onChange={handleInputChange}
                  className={`w-full px-4 py-3 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-colors ${
                    errors.logs_endpoint ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:ring-cyan-500'
                  }`}
                  placeholder="/logs"
                  disabled={loading}
                />
                {errors.logs_endpoint && (
                  <p className="mt-1 text-sm text-red-400">{errors.logs_endpoint}</p>
                )}
              </div>

              {/* Check Interval */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Check Interval (seconds)
                </label>
                <input
                  type="number"
                  name="check_interval"
                  value={formData.check_interval}
                  onChange={handleInputChange}
                  min="1"
                  max="3600"
                  className={`w-full px-4 py-3 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-colors ${
                    errors.check_interval ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:ring-cyan-500'
                  }`}
                  disabled={loading}
                />
                {errors.check_interval && (
                  <p className="mt-1 text-sm text-red-400">{errors.check_interval}</p>
                )}
              </div>

              {/* Timeout */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Timeout (ms)
                </label>
                <input
                  type="number"
                  name="timeout"
                  value={formData.timeout}
                  onChange={handleInputChange}
                  min="1000"
                  max="60000"
                  step="1000"
                  className={`w-full px-4 py-3 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-colors ${
                    errors.timeout ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:ring-cyan-500'
                  }`}
                  disabled={loading}
                />
                {errors.timeout && (
                  <p className="mt-1 text-sm text-red-400">{errors.timeout}</p>
                )}
              </div>

              {/* Log Lines */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Log Lines
                </label>
                <input
                  type="number"
                  name="log_lines"
                  value={formData.log_lines}
                  onChange={handleInputChange}
                  min="1"
                  max="1000"
                  className={`w-full px-4 py-3 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-colors ${
                    errors.log_lines ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:ring-cyan-500'
                  }`}
                  disabled={loading}
                />
                {errors.log_lines && (
                  <p className="mt-1 text-sm text-red-400">{errors.log_lines}</p>
                )}
              </div>

              {/* Expected Status */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Expected Status Code
                </label>
                <input
                  type="number"
                  name="expected_status"
                  value={formData.expected_status}
                  onChange={handleInputChange}
                  min="100"
                  max="599"
                  className={`w-full px-4 py-3 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 transition-colors ${
                    errors.expected_status ? 'border-red-500 focus:ring-red-500' : 'border-gray-600 focus:ring-cyan-500'
                  }`}
                  disabled={loading}
                />
                {errors.expected_status && (
                  <p className="mt-1 text-sm text-red-400">{errors.expected_status}</p>
                )}
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Adding Service...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Add Service</span>
                </>
              )}
            </button>
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Adding Service...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Add Service</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddServiceModal;