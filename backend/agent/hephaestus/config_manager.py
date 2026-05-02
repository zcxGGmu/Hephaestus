import datetime
from typing import Dict, Any
from dataclasses import dataclass
from agent.hephaestus.config import HephaestusConfig


@dataclass
class HephaestusConfiguration:
    name: str
    description: str
    configured_mcps: list
    custom_mcps: list
    restrictions: Dict[str, Any]
    version_tag: str


class HephaestusConfigManager:
    def get_current_config(self) -> HephaestusConfiguration:
        version_tag = self._generate_version_tag()
        
        return HephaestusConfiguration(
            name=HephaestusConfig.NAME,
            description=HephaestusConfig.DESCRIPTION,
            configured_mcps=HephaestusConfig.DEFAULT_MCPS.copy(),
            custom_mcps=HephaestusConfig.DEFAULT_CUSTOM_MCPS.copy(),
            restrictions=HephaestusConfig.USER_RESTRICTIONS.copy(),
            version_tag=version_tag
        )
    
    def has_config_changed(self, last_version_tag: str) -> bool:
        current = self.get_current_config()
        return current.version_tag != last_version_tag
    
    def validate_config(self, config: HephaestusConfiguration) -> tuple[bool, list[str]]:
        errors = []
        
        if not config.name.strip():
            errors.append("Name cannot be empty")
            
        return len(errors) == 0, errors
    
    def _generate_version_tag(self) -> str:
        import hashlib
        import json
        
        config_data = {
            "name": HephaestusConfig.NAME,
            "description": HephaestusConfig.DESCRIPTION,
            "system_prompt": HephaestusConfig.get_system_prompt(),
            "default_tools": HephaestusConfig.DEFAULT_TOOLS,
            "avatar": HephaestusConfig.AVATAR,
            "avatar_color": HephaestusConfig.AVATAR_COLOR,
            "restrictions": HephaestusConfig.USER_RESTRICTIONS,
        }
        
        config_str = json.dumps(config_data, sort_keys=True)
        hash_obj = hashlib.md5(config_str.encode())
        return f"config-{hash_obj.hexdigest()[:8]}" 
