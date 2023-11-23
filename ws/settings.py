from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional, Tuple, Union

import dotenv
import tomli
from pydantic import BaseSettings, Field, FilePath, validator
from rich.console import Console

ENV_FILE = '.ws.env'


class Settings(BaseSettings):
    connect_timeout: float = Field(5.0, gt=0)
    disconnect_timeout: float = Field(5.0, gt=0)
    response_timeout: float = Field(5.0, gt=0)
    message_queue_size: int = Field(1, ge=0)
    max_message_size: int = Field(1024 * 1024, gt=0)
    extra_headers: Optional[List[Tuple[str, str]]] = None
    terminal_width: int = Field(Console().width, gt=0)
    tls_ca_file: Optional[FilePath] = None
    tls_certificate_file: Optional[FilePath] = None
    tls_key_file: Optional[FilePath] = None
    tls_password: Optional[str] = None

    @validator('response_timeout', pre=True)
    def check_response_timeout(cls, value):
        if isinstance(value, str) and value.lower() == 'inf':
            return math.inf
        return value

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
    local_env_file = Path.cwd() / ENV_FILE
    home_env_file = Path.home() / ENV_FILE

    if pyproject_file.exists():
        settings = Settings()
        config = get_config_from_toml(pyproject_file)
        if config is None:
            return settings

        for item in Settings.__fields__.keys():
            if item in config:
                setattr(settings, item, config[item])

        return settings

    if local_env_file.exists():
        dotenv.load_dotenv(dotenv_path=local_env_file)
        return Settings()

    if home_env_file.exists():
        dotenv.load_dotenv(dotenv_path=home_env_file)
        return Settings()

    return Settings()
