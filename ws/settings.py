from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Union

import tomli
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    connect_timeout: float = Field(5.0, gt=0)
    disconnect_timeout: float = Field(5.0, gt=0)
    response_timeout: float = Field(5.0, gt=0)
    message_queue_size: int = Field(1, ge=0)
    max_message_size: int = Field(1024 * 1024, gt=0)
    receive_buffer: int = Field(4 * 1024, gt=0)
    extra_headers: Optional[Dict[str, str]] = None

    class Config:
        env_prefix = 'ws_'


def get_config_from_toml(filename: Union[str, Path]) -> Optional[dict[str, float]]:
    try:
        with open(filename, 'rb') as f:
            data = tomli.load(f)
    except tomli.TOMLDecodeError:
        return

    if 'tool' in data and 'ws' in data['tool']:
        return data['tool']['ws']


def get_settings() -> Settings:
    pyproject_file = Path.cwd() / 'pyproject.toml'
    settings = Settings()

    if pyproject_file.exists():
        config = get_config_from_toml(pyproject_file)
        if config is None:
            return settings

        for item in Settings.__fields__.keys():
            if item in config:
                setattr(settings, item, config[item])

    return settings
