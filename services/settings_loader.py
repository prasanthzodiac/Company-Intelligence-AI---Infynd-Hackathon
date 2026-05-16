"""Load config/settings.yaml with environment overrides for cloud deployment."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .llm_client import LLMConfig, llm_config_to_dict, merge_llm_config


def load_settings(base_dir: Path) -> Dict[str, Any]:
    config_path = base_dir / "config" / "settings.yaml"
    settings: Dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            settings = loaded if isinstance(loaded, dict) else {}

    llm_cfg = merge_llm_config(settings.get("llm"))
    settings["llm"] = llm_config_to_dict(llm_cfg)
    return settings


def get_llm_config(settings: Dict[str, Any]) -> LLMConfig:
    return merge_llm_config(settings.get("llm"))
