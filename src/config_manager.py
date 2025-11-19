import yaml
import os
from .utils import log_error

def load_config(config_path="config/settings.yaml"):
    if not os.path.exists(config_path):
        log_error(f"Config file not found at {config_path}")
        log_error("Please create it using the template provided.")
        exit(1)

    with open(config_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as exc:
            log_error(f"Error parsing YAML config: {exc}")
            exit(1)
