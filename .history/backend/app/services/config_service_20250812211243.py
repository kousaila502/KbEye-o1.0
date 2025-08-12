import json
import aiofiles
import os
from typing import List, Dict
from app.core.config import settings

class ConfigService:
    
    def __init__(self):
        self.services_file = os.path.join(settings.CONFIG_PATH, settings.SERVICES_CONFIG_FILE)
        self.alerts_file = os.path.join(settings.CONFIG_PATH, settings.ALERTS_CONFIG_FILE) 
        self.settings_file = os.path.join(settings.CONFIG_PATH, settings.SETTINGS_CONFIG_FILE)
    
    async def load_services_config(self) -> List[Dict]:
        """Load services from JSON config file"""
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
        """Save services to JSON config file"""
        try:
            os.makedirs(os.path.dirname(self.services_file), exist_ok=True)
            
            config_data = {"services": services}
            
            async with aiofiles.open(self.services_file, 'w') as f:
                await f.write(json.dumps(config_data, indent=2))
                
            print(f"✅ Services config saved to {self.services_file}")
        except Exception as e:
            print(f"❌ Error saving services config: {e}")
    
    async def sync_database_to_config(self, services_from_db: List[Dict]):
        """Sync database services to config file"""
        await self.save_services_config(services_from_db)

# Global config service instance
config_service = ConfigService()