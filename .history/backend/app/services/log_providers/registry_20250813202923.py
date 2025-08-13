# app/services/log_providers/registry.py

import importlib
import inspect
import os
from typing import Dict, List, Type, Optional, Any
from app.services.log_providers.base import BaseLogProvider, LogProviderConfig, LogResponse, LogProviderError

class LogProviderRegistry:
    """
    Registry for managing all available log providers.
    
    Automatically discovers and manages platform-specific log providers,
    provides unified interface for fetching logs from any platform.
    """
    
    def __init__(self):
        self._providers: Dict[str, Type[BaseLogProvider]] = {}
        self._instances: Dict[str, BaseLogProvider] = {}
        self._auto_discover()
    
    def _auto_discover(self):
        """
        Automatically discover all log providers in the log_providers directory.
        
        Scans for Python files containing classes that inherit from BaseLogProvider.
        """
        providers_dir = os.path.dirname(__file__)
        
        # Get all Python files in the log_providers directory
        for filename in os.listdir(providers_dir):
            if filename.endswith('.py') and filename not in ['__init__.py', 'base.py', 'registry.py']:
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    module_path = f"app.services.log_providers.{module_name}"
                    module = importlib.import_module(module_path)
                    
                    # Find all classes that inherit from BaseLogProvider
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseLogProvider) and 
                            obj != BaseLogProvider and 
                            not inspect.isabstract(obj)):
                            
                            # Create an instance to get the platform_type
                            try:
                                instance = obj()
                                platform_type = instance.platform_type
                                self._providers[platform_type] = obj
                                print(f"✅ Discovered log provider: {platform_type} ({obj.__name__})")
                            except Exception as e:
                                print(f"❌ Failed to instantiate provider {obj.__name__}: {e}")
                                
                except ImportError as e:
                    print(f"❌ Failed to import log provider module {module_name}: {e}")
                except Exception as e:
                    print(f"❌ Error discovering providers in {module_name}: {e}")
    
    def register_provider(self, provider_class: Type[BaseLogProvider]) -> bool:
        """
        Manually register a log provider.
        
        Args:
            provider_class: Class that inherits from BaseLogProvider
            
        Returns:
            bool: True if registration successful
        """
        try:
            if not issubclass(provider_class, BaseLogProvider):
                raise ValueError(f"{provider_class.__name__} must inherit from BaseLogProvider")
            
            if inspect.isabstract(provider_class):
                raise ValueError(f"{provider_class.__name__} is abstract and cannot be registered")
            
            # Create instance to get platform type
            instance = provider_class()
            platform_type = instance.platform_type
            
            self._providers[platform_type] = provider_class
            print(f"✅ Manually registered log provider: {platform_type} ({provider_class.__name__})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register provider {provider_class.__name__}: {e}")
            return False
    
    def get_provider(self, platform_type: str) -> Optional[BaseLogProvider]:
        """
        Get a log provider instance for the specified platform.
        
        Args:
            platform_type: Platform identifier (e.g., 'heroku', 'aws', 'azure')
            
        Returns:
            BaseLogProvider: Provider instance or None if not found
        """
        if platform_type not in self._providers:
            return None
        
        # Use cached instance if available
        if platform_type in self._instances:
            return self._instances[platform_type]
        
        # Create new instance
        try:
            provider_class = self._providers[platform_type]
            instance = provider_class()
            self._instances[platform_type] = instance
            return instance
        except Exception as e:
            print(f"❌ Failed to create provider instance for {platform_type}: {e}")
            return None
    
    def list_available_platforms(self) -> List[str]:
        """
        Get list of all available platform types.
        
        Returns:
            List[str]: List of platform identifiers
        """
        return list(self._providers.keys())
    
    def is_platform_supported(self, platform_type: str) -> bool:
        """
        Check if a platform is supported.
        
        Args:
            platform_type: Platform identifier
            
        Returns:
            bool: True if platform is supported
        """
        return platform_type in self._providers
    
    def get_platform_capabilities(self, platform_type: str) -> Dict[str, Any]:
        """
        Get capabilities of a specific platform.
        
        Args:
            platform_type: Platform identifier
            
        Returns:
            Dict: Platform capabilities or empty dict if not found
        """
        provider = self.get_provider(platform_type)
        if provider:
            return provider.get_capabilities()
        return {}
    
    def get_all_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """
        Get capabilities of all available platforms.
        
        Returns:
            Dict: Platform capabilities mapped by platform type
        """
        capabilities = {}
        for platform_type in self._providers.keys():
            capabilities[platform_type] = self.get_platform_capabilities(platform_type)
        return capabilities
    
    async def fetch_logs(
        self, 
        platform_type: str, 
        config: LogProviderConfig, 
        lines: int = 50
    ) -> LogResponse:
        """
        Fetch logs from any platform using the appropriate provider.
        
        Args:
            platform_type: Platform identifier
            config: Service configuration
            lines: Number of log lines to fetch
            
        Returns:
            LogResponse: Standardized log response
            
        Raises:
            LogProviderError: If platform not supported or fetch fails
        """
        provider = self.get_provider(platform_type)
        if not provider:
            raise LogProviderError(
                f"Platform '{platform_type}' is not supported. "
                f"Available platforms: {', '.join(self.list_available_platforms())}",
                "PLATFORM_NOT_SUPPORTED"
            )
        
        return await provider.fetch_logs(config, lines)
    
    async def validate_service_config(
        self, 
        platform_type: str, 
        config: Dict[str, Any]
    ) -> bool:
        """
        Validate service configuration for a specific platform.
        
        Args:
            platform_type: Platform identifier
            config: Configuration to validate
            
        Returns:
            bool: True if configuration is valid
            
        Raises:
            LogProviderError: If platform not supported
            ValueError: If configuration is invalid
        """
        provider = self.get_provider(platform_type)
        if not provider:
            raise LogProviderError(
                f"Platform '{platform_type}' is not supported",
                "PLATFORM_NOT_SUPPORTED"
            )
        
        return provider.validate_config(config)
    
    async def test_authentication(
        self, 
        platform_type: str, 
        credentials: Dict[str, Any]
    ) -> bool:
        """
        Test authentication for a specific platform.
        
        Args:
            platform_type: Platform identifier
            credentials: Authentication credentials
            
        Returns:
            bool: True if authentication successful
            
        Raises:
            LogProviderError: If platform not supported or auth fails
        """
        provider = self.get_provider(platform_type)
        if not provider:
            raise LogProviderError(
                f"Platform '{platform_type}' is not supported",
                "PLATFORM_NOT_SUPPORTED"
            )
        
        return await provider.authenticate(credentials)
    
    def get_registry_status(self) -> Dict[str, Any]:
        """
        Get status information about the registry.
        
        Returns:
            Dict: Registry status and statistics
        """
        return {
            "total_providers": len(self._providers),
            "active_instances": len(self._instances),
            "available_platforms": self.list_available_platforms(),
            "provider_classes": {
                platform: provider.__name__ 
                for platform, provider in self._providers.items()
            }
        }
    
    def reload_providers(self):
        """
        Reload all providers (useful for development).
        
        Clears current providers and re-discovers them.
        """
        print("🔄 Reloading log providers...")
        self._providers.clear()
        self._instances.clear()
        self._auto_discover()
        print(f"✅ Reloaded {len(self._providers)} providers")

class LogProviderFactory:
    """
    Factory class for creating log provider configurations and managing the registry.
    
    Provides convenient methods for working with log providers without directly
    interacting with the registry.
    """
    
    def __init__(self, registry: LogProviderRegistry = None):
        self.registry = registry or LogProviderRegistry()
    
    def create_config(
        self,
        service_id: str,
        platform_type: str,
        app_name: str,
        credentials: Dict[str, Any],
        parameters: Dict[str, Any] = None
    ) -> LogProviderConfig:
        """
        Create a log provider configuration.
        
        Args:
            service_id: Service identifier
            platform_type: Platform type
            app_name: Application name on the platform
            credentials: Authentication credentials
            parameters: Additional platform-specific parameters
            
        Returns:
            LogProviderConfig: Configuration object
        """
        return LogProviderConfig(
            service_id=service_id,
            platform_type=platform_type,
            app_name=app_name,
            credentials=credentials,
            parameters=parameters or {}
        )
    
    async def fetch_logs_by_service_id(
        self,
        service_id: str,
        platform_config: Dict[str, Any],
        lines: int = 50
    ) -> LogResponse:
        """
        Fetch logs for a service using its platform configuration.
        
        Args:
            service_id: Service identifier
            platform_config: Platform configuration from service
            lines: Number of lines to fetch
            
        Returns:
            LogResponse: Log response
        """
        config = self.create_config(
            service_id=service_id,
            platform_type=platform_config.get("type"),
            app_name=platform_config.get("app_name"),
            credentials=platform_config.get("credentials", {}),
            parameters=platform_config.get("parameters", {})
        )
        
        return await self.registry.fetch_logs(
            platform_type=config.platform_type,
            config=config,
            lines=lines
        )
    
    def get_supported_platforms(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about all supported platforms.
        
        Returns:
            List[Dict]: Platform information including capabilities
        """
        platforms = []
        for platform_type in self.registry.list_available_platforms():
            capabilities = self.registry.get_platform_capabilities(platform_type)
            platforms.append({
                "type": platform_type,
                "capabilities": capabilities,
                "provider_class": self.registry._providers[platform_type].__name__
            })
        return platforms

# Global registry instance
log_provider_registry = LogProviderRegistry()
log_provider_factory = LogProviderFactory(log_provider_registry)