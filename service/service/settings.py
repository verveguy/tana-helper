# TODO: figure out how to make settings more modular, based on endpoints configured
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

import os
from pathlib import Path
from typing_extensions import Annotated


class Settings(BaseSettings):
  """
  Settings for Tana Helper
  """
  # Read from .env for development/debug only
  # otherwise, see below for get_settings() function
  model_config = SettingsConfigDict( title="Settings", env_file='.env', env_file_encoding='utf-8')

  openai_api_key: Annotated[str, Field(title="OpenAI API Key",
    description="API Key for OpenAI. You can also pass this as the header x-openai-api-key on each request.")] \
      = "OPENAI_API_KEY NOT SET"

  tana_api_token: Annotated[str, Field(title="Tana API Token",
    description="API Token for Tana access. You can also pass this as the header x-tana-api-token on each request.")] \
      = "TANA_API_TOKEN NOT SET"

  webhook_template_path: Annotated[str, Field(title="Webhook Template Path",
      description="Path to store webhook templates")] \
        = os.path.join(Path.home(), '.tana_helper', 'webhooks')

  temp_files: Annotated[str, Field(title="Temporary Files Path",
    description="Path to store temporary files")] \
      = os.path.join('/', 'tmp','tana_helper', 'tmp')

  export_path: Annotated[str, Field(title="Export Path",
    description="Path to store exported files")] \
      = os.path.join('/', 'tmp','tana_helper', 'export')

  tana_environment: Annotated[str, Field(title="Tana Pinecone Environment",
    description="Pinecone environment for Tana vector storage")] \
      = "us-west4-gcp-free"

  tana_namespace: Annotated[str, Field(title="Tana VectorDB Namespace",
    description="VectorDB namespace for Tana vector storage")] \
      = "tana-namespace"

  tana_index: Annotated[str, Field(title="Tana VectorDB Index",
    description="VectorDB index for Tana vector storage")] \
      = "tana-helper"
  
# create global settings 
# TODO: make settings per-request context, not gobal
global settings

tana_helper_config_dir = os.path.join(Path.home(), '.tana_helper')
settings_path = os.path.join(tana_helper_config_dir, 'settings.json')

def get_settings():
  global settings
  try:
    with open(settings_path, 'r') as f:
      settings_dict = json.load(f)
      settings = Settings.model_validate(settings_dict)
  except Exception:
    # any exception, reset to defaults
    settings = Settings()
  return settings

def set_settings(new_settings:Settings):
  global settings
  settings = new_settings
  # write new settings to .env file
  if not os.path.exists(tana_helper_config_dir):
      os.makedirs(tana_helper_config_dir, exist_ok=True)
  with open(settings_path, 'w') as f:
    f.write(settings.model_dump_json())
  return settings


# read from file to start with
settings = get_settings()
