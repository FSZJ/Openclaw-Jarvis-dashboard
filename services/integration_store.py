"""Persistent storage for provider integrations."""
import json
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any, Dict

from config import INTEGRATIONS_FILE


class IntegrationStore:
    """File-backed storage for model provider credentials and settings."""

    _lock = Lock()

    @classmethod
    def _default_payload(cls) -> Dict[str, Any]:
        return {
            "version": 1,
            "providers": {
                "minimax": {
                    "enabled": False,
                    "api_key": "",
                    "group_id": "",
                    "quota_url": "",
                    "usage_is_remaining": False,
                },
                "openai": {
                    "enabled": False,
                    "api_key": "",
                    "project_id": "",
                    "organization_id": "",
                },
                "gemini": {
                    "enabled": False,
                    "api_key": "",
                    "project_id": "",
                },
                "glm": {
                    "enabled": False,
                    "api_key": "",
                    "base_url": "https://open.bigmodel.cn/api/paas/v4",
                },
            },
        }

    @classmethod
    def _ensure_file(cls):
        if INTEGRATIONS_FILE.exists():
            return
        INTEGRATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        INTEGRATIONS_FILE.write_text(json.dumps(cls._default_payload(), ensure_ascii=False, indent=2))
        try:
            INTEGRATIONS_FILE.chmod(0o600)
        except Exception:
            pass

    @classmethod
    def _load(cls) -> Dict[str, Any]:
        cls._ensure_file()
        try:
            payload = json.loads(INTEGRATIONS_FILE.read_text() or "{}")
        except Exception:
            payload = cls._default_payload()

        if not isinstance(payload, dict):
            payload = cls._default_payload()

        default = cls._default_payload()
        payload.setdefault("version", default["version"])
        payload.setdefault("providers", {})

        providers = payload["providers"]
        for provider, defaults in default["providers"].items():
            current = providers.get(provider)
            if not isinstance(current, dict):
                providers[provider] = deepcopy(defaults)
                continue
            merged = deepcopy(defaults)
            merged.update(current)
            providers[provider] = merged

        return payload

    @classmethod
    def _save(cls, payload: Dict[str, Any]):
        INTEGRATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        INTEGRATIONS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        try:
            INTEGRATIONS_FILE.chmod(0o600)
        except Exception:
            pass

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        with cls._lock:
            return cls._load()

    @classmethod
    def update_all(cls, providers: Dict[str, Any]) -> Dict[str, Any]:
        with cls._lock:
            payload = cls._load()
            for provider, cfg in (providers or {}).items():
                if provider not in payload["providers"] or not isinstance(cfg, dict):
                    continue
                merged = deepcopy(payload["providers"][provider])
                for key, value in cfg.items():
                    # Keep existing secret when UI intentionally sends empty string.
                    if key == "api_key" and isinstance(value, str) and value.strip() == "":
                        continue
                    merged[key] = value
                payload["providers"][provider] = merged
            cls._save(payload)
            return payload

    @classmethod
    def get_public_view(cls) -> Dict[str, Any]:
        payload = cls.get_all()
        public_payload = deepcopy(payload)

        def mask(secret: str) -> str:
            if not secret:
                return ""
            if len(secret) <= 8:
                return "*" * len(secret)
            return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"

        for provider_cfg in public_payload.get("providers", {}).values():
            if not isinstance(provider_cfg, dict):
                continue
            if "api_key" in provider_cfg:
                raw = str(provider_cfg.get("api_key") or "")
                provider_cfg["api_key_masked"] = mask(raw)
                provider_cfg["has_api_key"] = bool(raw.strip())
                provider_cfg.pop("api_key", None)

        return public_payload
