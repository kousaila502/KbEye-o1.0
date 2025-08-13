import json
import aiofiles
import os
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings

class ConfigService:
    
    def __init__(self):
        # Legacy files (for backward compatibility)
        self.services_file = os.path.join(settings.CONFIG_PATH, settings.SERVICES_CONFIG_FILE)
        self.alerts_file = os.path.join(settings.CONFIG_PATH, settings.ALERTS_CONFIG_FILE) 
        self.settings_file = os.path.join(settings.CONFIG_PATH, settings.SETTINGS_CONFIG_FILE)
        
        # New individual config directories
        self.services_dir = os.path.join(settings.CONFIG_PATH, "services")
        self.alerts_dir = os.path.join(settings.CONFIG_PATH, "alerts")
        self.templates_dir = os.path.join(settings.CONFIG_PATH, "templates")
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create config directory structure if it doesn't exist"""
        directories = [
            settings.CONFIG_PATH,
            self.services_dir,
            self.alerts_dir,
            self.templates_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _get_service_config_path(self, service_id: str) -> str:
        """Get path for individual service config file"""
        return os.path.join(self.services_dir, f"{service_id}.json")
    
    def _get_service_alerts_path(self, service_id: str) -> str:
        """Get path for individual service alerts config file"""
        return os.path.join(self.alerts_dir, f"{service_id}-alerts.json")
    
    async def create_service_template(self):
        """Create a template file for new services"""
        template_path = os.path.join(self.templates_dir, "service-template.json")
        
        template_data = {
            "_description": "Template for new service configuration",
            "_usage": "Copy this template and modify for new services",
            "service_id": "example-service",
            "name": "Example Service",
            "url": "https://api.example.com",
            "health_endpoint": "/health",
            "logs_endpoint": "/logs",
            "check_interval": 30,
            "log_lines": 50,
            "timeout": 5000,
            "expected_status": 200,
            "ssl_verify": True,
            "tags": ["production", "api"],
            "description": "Service description",
            "owner": "team@company.com",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            async with aiofiles.open(template_path, 'w') as f:
                await f.write(json.dumps(template_data, indent=2))
            print(f"✅ Service template created at {template_path}")
        except Exception as e:
            print(f"❌ Error creating service template: {e}")
    
    # ============= INDIVIDUAL SERVICE CONFIG METHODS =============
    
    async def load_service_config(self, service_id: str) -> Optional[Dict]:
        """Load configuration for a specific service"""
        config_path = self._get_service_config_path(service_id)
        
        try:
            if os.path.exists(config_path):
                async with aiofiles.open(config_path, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            return None
        except Exception as e:
            print(f"Error loading config for service {service_id}: {e}")
            return None
    
    async def save_service_config(self, service_id: str, config_data: Dict):
        """Save configuration for a specific service"""
        config_path = self._get_service_config_path(service_id)
        
        # Add metadata
        config_data["updated_at"] = datetime.utcnow().isoformat()
        if "created_at" not in config_data:
            config_data["created_at"] = datetime.utcnow().isoformat()
        
        try:
            async with aiofiles.open(config_path, 'w') as f:
                await f.write(json.dumps(config_data, indent=2))
            print(f"✅ Service config saved: {config_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving config for service {service_id}: {e}")
            return False
    
    async def delete_service_config(self, service_id: str) -> bool:
        """Delete configuration file for a service"""
        config_path = self._get_service_config_path(service_id)
        alerts_path = self._get_service_alerts_path(service_id)
        
        deleted_files = []
        
        # Delete service config
        if os.path.exists(config_path):
            try:
                os.remove(config_path)
                deleted_files.append("config")
            except Exception as e:
                print(f"❌ Error deleting service config: {e}")
                return False
        
        # Delete alerts config
        if os.path.exists(alerts_path):
            try:
                os.remove(alerts_path)
                deleted_files.append("alerts")
            except Exception as e:
                print(f"❌ Error deleting service alerts: {e}")
        
        if deleted_files:
            print(f"✅ Deleted {service_id} files: {', '.join(deleted_files)}")
        
        return True
    
    async def list_service_configs(self) -> List[str]:
        """List all service IDs that have individual config files"""
        service_ids = []
        
        try:
            if os.path.exists(self.services_dir):
                for filename in os.listdir(self.services_dir):
                    if filename.endswith('.json') and not filename.startswith('_'):
                        service_id = filename[:-5]  # Remove .json extension
                        service_ids.append(service_id)
        except Exception as e:
            print(f"Error listing service configs: {e}")
        
        return sorted(service_ids)
    
    # ============= SERVICE ALERTS CONFIG METHODS =============
    
    async def load_service_alerts_config(self, service_id: str) -> Dict:
        """Load alerts configuration for a specific service"""
        alerts_path = self._get_service_alerts_path(service_id)
        
        try:
            if os.path.exists(alerts_path):
                async with aiofiles.open(alerts_path, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            else:
                # Return default alerts config
                return self._get_default_alerts_config(service_id)
        except Exception as e:
            print(f"Error loading alerts config for service {service_id}: {e}")
            return self._get_default_alerts_config(service_id)
    
    async def save_service_alerts_config(self, service_id: str, alerts_config: Dict):
        """Save alerts configuration for a specific service"""
        alerts_path = self._get_service_alerts_path(service_id)
        
        # Add metadata
        alerts_config["updated_at"] = datetime.utcnow().isoformat()
        if "created_at" not in alerts_config:
            alerts_config["created_at"] = datetime.utcnow().isoformat()
        
        try:
            async with aiofiles.open(alerts_path, 'w') as f:
                await f.write(json.dumps(alerts_config, indent=2))
            print(f"✅ Service alerts config saved: {alerts_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving alerts config for service {service_id}: {e}")
            return False
    
    def _get_default_alerts_config(self, service_id: str) -> Dict:
        """Get default alerts configuration for a service"""
        return {
            "service_id": service_id,
            "enabled": True,
            "cooldown_minutes": 5,
            "failure_threshold": 1,
            "alert_types": {
                "service_down": {
                    "enabled": True,
                    "severity": "critical",
                    "notify_email": True,
                    "notify_webhook": False
                },
                "service_slow": {
                    "enabled": False,
                    "severity": "warning",
                    "threshold_ms": 5000,
                    "notify_email": False,
                    "notify_webhook": False
                }
            },
            "email_config": {
                "enabled": True,
                "recipients": [],
                "subject_prefix": "[KbEye Alert]"
            },
            "webhook_config": {
                "enabled": False,
                "url": "",
                "headers": {}
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    # ============= SYNC METHODS =============
    
    async def sync_database_to_individual_configs(self, services_from_db: List[Dict]):
        """Sync database services to individual config files"""
        synced_count = 0
        
        for service_data in services_from_db:
            service_id = service_data.get("service_id")
            if service_id:
                success = await self.save_service_config(service_id, service_data)
                if success:
                    synced_count += 1
                
                # Create default alerts config if it doesn't exist
                alerts_path = self._get_service_alerts_path(service_id)
                if not os.path.exists(alerts_path):
                    default_alerts = self._get_default_alerts_config(service_id)
                    await self.save_service_alerts_config(service_id, default_alerts)
        
        print(f"✅ Synced {synced_count} services to individual config files")
        return synced_count
    
    async def sync_service_from_database(self, service_data: Dict) -> bool:
        """Sync a single service from database to its config file"""
        service_id = service_data.get("service_id")
        if not service_id:
            return False
        
        return await self.save_service_config(service_id, service_data)
    
    # ============= LEGACY METHODS (for backward compatibility) =============
    
    async def load_services_config(self) -> List[Dict]:
        """Load services from legacy JSON config file"""
        try:
            if os.path.exists(self.services_file):
                async with aiofiles.open(self.services_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    return data.get('services', [])
            return []
        except Exception as e:
            print(f"Error loading services config: {e}")
            return []
    
    async def save_services_config(self, services: List[Dict]):
        """Save services to legacy JSON config file"""
        try:
            os.makedirs(os.path.dirname(self.services_file), exist_ok=True)
            
            config_data = {"services": services}
            
            async with aiofiles.open(self.services_file, 'w') as f:
                await f.write(json.dumps(config_data, indent=2))
                
            print(f"✅ Legacy services config saved to {self.services_file}")
        except Exception as e:
            print(f"❌ Error saving services config: {e}")
    
    async def sync_database_to_config(self, services_from_db: List[Dict]):
        """Sync database services to legacy config file (backward compatibility)"""
        await self.save_services_config(services_from_db)
    
    # ============= UTILITY METHODS =============
    
    async def get_config_summary(self) -> Dict:
        """Get summary of all configuration files"""
        service_configs = await self.list_service_configs()
        
        # Count alerts configs
        alerts_count = 0
        if os.path.exists(self.alerts_dir):
            alerts_files = [f for f in os.listdir(self.alerts_dir) if f.endswith('-alerts.json')]
            alerts_count = len(alerts_files)
        
        return {
            "config_path": settings.CONFIG_PATH,
            "individual_service_configs": len(service_configs),
            "service_configs_list": service_configs,
            "alerts_configs": alerts_count,
            "legacy_files": {
                "services.json": os.path.exists(self.services_file),
                "alerts.json": os.path.exists(self.alerts_file),
                "settings.json": os.path.exists(self.settings_file)
            },
            "directories": {
                "services": os.path.exists(self.services_dir),
                "alerts": os.path.exists(self.alerts_dir),
                "templates": os.path.exists(self.templates_dir)
            }
        }

# Global config service instance
config_service = ConfigService()