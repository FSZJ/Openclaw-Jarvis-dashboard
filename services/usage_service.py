"""Multi-provider usage aggregation service."""
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from config import MINIMAX_API_KEY, MINIMAX_GROUP_ID, MINIMAX_QUOTA_URL, MINIMAX_USAGE_IS_REMAINING
from services.integration_store import IntegrationStore


class UsageService:
    """Build normalized usage panels for configured providers."""

    _cache: Optional[Tuple[float, List[Dict[str, Any]]]] = None
    _cache_ttl_seconds = 15
    _provider_order = ["minimax", "openai", "gemini", "glm"]
    _provider_titles = {
        "minimax": "MiniMax",
        "openai": "OpenAI",
        "gemini": "Gemini",
        "glm": "GLM",
    }

    @classmethod
    def _request_json(cls, url: str, headers: Dict[str, str], timeout: int = 6) -> Dict[str, Any]:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @classmethod
    def _as_bool(cls, value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off", ""}:
                return False
        return default

    @classmethod
    def _effective_provider_cfg(cls, provider: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(cfg or {})
        if provider == "minimax":
            out["api_key"] = str(out.get("api_key") or MINIMAX_API_KEY or "").strip()
            out["group_id"] = str(out.get("group_id") or MINIMAX_GROUP_ID or "").strip()
            out["quota_url"] = str(out.get("quota_url") or MINIMAX_QUOTA_URL or "").strip()
            out["usage_is_remaining"] = cls._as_bool(
                out.get("usage_is_remaining"),
                default=MINIMAX_USAGE_IS_REMAINING
            )
        return out

    @classmethod
    def _missing_required_fields(cls, provider: str, cfg: Dict[str, Any]) -> List[str]:
        required = {
            "minimax": ["api_key", "quota_url"],
            "openai": ["api_key"],
            "gemini": ["api_key"],
            "glm": ["api_key"],
        }.get(provider, [])
        missing = []
        for field in required:
            value = cfg.get(field)
            if value is None or str(value).strip() == "":
                missing.append(field)
        return missing

    @classmethod
    def _empty_panel(cls, provider: str, missing_fields: List[str]) -> Dict[str, Any]:
        title = cls._provider_titles.get(provider, provider)
        label_map = {
            "api_key": "API Key",
            "quota_url": "Quota URL",
            "group_id": "Group ID",
        }
        human_missing = [label_map.get(item, item) for item in missing_fields]
        message = "该模型已开启，但尚未完成 API 配置"
        if human_missing:
            message += f"（缺少：{', '.join(human_missing)}）"

        return {
            "key": provider,
            "title": title,
            "type": "empty",
            "panel_state": "empty",
            "source": "待配置",
            "status": "pending",
            "message": message,
            "missing_fields": missing_fields,
            "used": None,
            "total": None,
            "percent": None,
            "remaining_text": None,
            "refresh_window": None,
            "models": [],
            "model": title,
            "running_tasks": 0,
            "running_agents": 0,
            "metric_status": "配置未完成",
            "updated_at": datetime.utcnow().isoformat(),
            "notes": None,
        }

    @classmethod
    def _error_panel(cls, provider: str, source: str, err: Exception, running_tasks: int = 0, running_agents: int = 0) -> Dict[str, Any]:
        title = cls._provider_titles.get(provider, provider)
        msg = cls._safe_error(err)
        return {
            "key": provider,
            "title": title,
            "type": "status",
            "panel_state": "error",
            "source": source,
            "status": "error",
            "message": f"配置已保存，但当前请求失败：{msg}",
            "missing_fields": [],
            "model": title,
            "running_tasks": running_tasks,
            "running_agents": running_agents,
            "metric_status": "不可用",
            "used": None,
            "total": None,
            "percent": None,
            "remaining_text": None,
            "refresh_window": None,
            "models": [],
            "updated_at": datetime.utcnow().isoformat(),
            "notes": msg,
        }

    @classmethod
    def _build_minimax_panel(cls, cfg: Dict[str, Any]) -> Dict[str, Any]:
        api_key = str(cfg.get("api_key") or "").strip()
        quota_url = str(cfg.get("quota_url") or "").strip()
        group_id = str(cfg.get("group_id") or "").strip()
        usage_is_remaining = cls._as_bool(
            cfg.get("usage_is_remaining"),
            default=MINIMAX_USAGE_IS_REMAINING
        )

        if "{group_id}" in quota_url and group_id:
            quota_url = quota_url.format(group_id=group_id)

        payload = cls._request_json(
            quota_url,
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        model_remains = data.get("model_remains") or []
        if not isinstance(model_remains, list):
            model_remains = []

        models = []
        total_sum = 0
        used_sum = 0
        remaining_sum = 0
        window_end = None

        for item in model_remains:
            try:
                total = int(item.get("current_interval_total_count") or 0)
                usage_raw = int(item.get("current_interval_usage_count") or 0)
            except (TypeError, ValueError):
                total = 0
                usage_raw = 0

            if usage_is_remaining:
                remaining = max(usage_raw, 0)
                used = max(total - remaining, 0)
            else:
                used = max(usage_raw, 0)
                remaining = max(total - used, 0)

            total_sum += total
            used_sum += used
            remaining_sum += remaining

            end_time = item.get("end_time")
            if window_end is None and end_time is not None:
                window_end = end_time

            model_name = item.get("model_name")
            if model_name:
                models.append(model_name)

        percent = round((used_sum / total_sum) * 100, 1) if total_sum > 0 else None

        remain_text = None
        if window_end:
            remain_ms = max(int(window_end) - int(time.time() * 1000), 0)
            remain_text = cls._human_duration(remain_ms)

        return {
            "key": "minimax",
            "title": "MiniMax",
            "type": "quota",
            "panel_state": "ready",
            "source": "真实计数",
            "status": "ok",
            "message": None,
            "missing_fields": [],
            "used": used_sum,
            "total": total_sum,
            "percent": percent,
            "remaining_text": str(remaining_sum),
            "refresh_window": remain_text,
            "models": models[:8],
            "updated_at": datetime.utcnow().isoformat(),
            "notes": None,
        }

    @classmethod
    def _build_openai_panel(cls, cfg: Dict[str, Any]) -> Dict[str, Any]:
        api_key = str(cfg.get("api_key") or "").strip()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if cfg.get("project_id"):
            headers["OpenAI-Project"] = str(cfg["project_id"])
        if cfg.get("organization_id"):
            headers["OpenAI-Organization"] = str(cfg["organization_id"])

        end_ts = int(time.time())
        start_ts = end_ts - 86400
        url = (
            "https://api.openai.com/v1/organization/usage/completions"
            f"?start_time={start_ts}&end_time={end_ts}&bucket_width=1d"
        )

        payload = cls._request_json(url, headers)
        rows = payload.get("data") if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            rows = []

        used_requests = 0
        model_names = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            result_rows = row.get("results") if isinstance(row.get("results"), list) else []
            for result in result_rows:
                if not isinstance(result, dict):
                    continue
                used_requests += int(result.get("num_model_requests") or 0)
                model_name = result.get("model")
                if model_name:
                    model_names.add(str(model_name))

        return {
            "key": "openai",
            "title": "OpenAI",
            "type": "quota",
            "panel_state": "ready",
            "source": "官方Usage API",
            "status": "ok",
            "message": None,
            "missing_fields": [],
            "used": used_requests,
            "total": None,
            "percent": None,
            "remaining_text": None,
            "refresh_window": "24h滚动窗口",
            "models": sorted(model_names)[:8],
            "updated_at": datetime.utcnow().isoformat(),
            "notes": "当前展示请求量（近24h）",
        }

    @classmethod
    def _build_gemini_panel(cls, cfg: Dict[str, Any], running_tasks: int, running_agents: int) -> Dict[str, Any]:
        api_key = str(cfg.get("api_key") or "").strip()
        cls._request_json(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={quote(api_key)}",
            {"Content-Type": "application/json"},
        )

        return {
            "key": "gemini",
            "title": "Gemini",
            "type": "status",
            "panel_state": "status_only",
            "source": "状态摘要",
            "status": "ok",
            "message": "计数源待接入",
            "missing_fields": [],
            "model": "Gemini",
            "running_tasks": running_tasks,
            "running_agents": running_agents,
            "metric_status": "计数源待接入",
            "used": None,
            "total": None,
            "percent": None,
            "remaining_text": None,
            "refresh_window": None,
            "models": [],
            "updated_at": datetime.utcnow().isoformat(),
            "notes": None,
        }

    @classmethod
    def _build_glm_panel(cls, cfg: Dict[str, Any], running_tasks: int, running_agents: int) -> Dict[str, Any]:
        api_key = str(cfg.get("api_key") or "").strip()
        base_url = str(cfg.get("base_url") or "https://open.bigmodel.cn/api/paas/v4").rstrip("/")
        cls._request_json(
            f"{base_url}/models",
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        return {
            "key": "glm",
            "title": "GLM",
            "type": "status",
            "panel_state": "status_only",
            "source": "状态摘要",
            "status": "ok",
            "message": "计数源待接入",
            "missing_fields": [],
            "model": "GLM",
            "running_tasks": running_tasks,
            "running_agents": running_agents,
            "metric_status": "计数源待接入",
            "used": None,
            "total": None,
            "percent": None,
            "remaining_text": None,
            "refresh_window": None,
            "models": [],
            "updated_at": datetime.utcnow().isoformat(),
            "notes": None,
        }

    @classmethod
    def _safe_error(cls, err: Exception) -> str:
        if isinstance(err, HTTPError):
            return f"HTTP {err.code}"
        if isinstance(err, URLError):
            return "网络不可达"
        return "请求失败"

    @classmethod
    def _human_duration(cls, remain_ms: int) -> str:
        seconds = max(remain_ms // 1000, 0)
        hours, rem = divmod(seconds, 3600)
        minutes, _ = divmod(rem, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @classmethod
    def get_usage_panels(cls, running_tasks: int = 0, running_agents: int = 0) -> List[Dict[str, Any]]:
        now = time.time()
        if cls._cache and (now - cls._cache[0]) < cls._cache_ttl_seconds:
            return cls._cache[1]

        cfg = IntegrationStore.get_all().get("providers", {})
        panels: List[Dict[str, Any]] = []

        for provider in cls._provider_order:
            raw_cfg = cfg.get(provider, {})
            if not bool(raw_cfg.get("enabled")):
                continue

            effective_cfg = cls._effective_provider_cfg(provider, raw_cfg)
            missing = cls._missing_required_fields(provider, effective_cfg)
            if missing:
                panels.append(cls._empty_panel(provider, missing))
                continue

            try:
                if provider == "minimax":
                    panel = cls._build_minimax_panel(effective_cfg)
                elif provider == "openai":
                    panel = cls._build_openai_panel(effective_cfg)
                elif provider == "gemini":
                    panel = cls._build_gemini_panel(effective_cfg, running_tasks, running_agents)
                elif provider == "glm":
                    panel = cls._build_glm_panel(effective_cfg, running_tasks, running_agents)
                else:
                    continue
                panels.append(panel)
            except Exception as err:
                source = "真实计数" if provider in {"minimax", "openai"} else "状态摘要"
                panels.append(cls._error_panel(provider, source, err, running_tasks, running_agents))

        cls._cache = (now, panels)
        return panels

    @classmethod
    def invalidate_cache(cls):
        cls._cache = None

    @classmethod
    def validate_provider(cls, provider: str, draft_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        saved = IntegrationStore.get_all().get("providers", {}).get(provider)
        if not saved:
            return {"success": False, "message": "不支持的 provider"}

        merged = dict(saved)
        if isinstance(draft_config, dict):
            clear_api_key = bool(draft_config.get("__clear_api_key"))
            for key, value in draft_config.items():
                if key.startswith("__"):
                    continue
                if key == "api_key" and isinstance(value, str) and value.strip() == "":
                    if clear_api_key:
                        merged[key] = ""
                        continue
                    continue
                merged[key] = value

        effective_cfg = cls._effective_provider_cfg(provider, merged)
        missing = cls._missing_required_fields(provider, effective_cfg)
        if missing:
            labels = {
                "api_key": "API Key",
                "quota_url": "Quota URL",
                "group_id": "Group ID",
            }
            miss = ", ".join(labels.get(item, item) for item in missing)
            return {"success": False, "message": f"配置不完整：缺少 {miss}"}

        try:
            if provider == "minimax":
                panel = cls._build_minimax_panel(effective_cfg)
            elif provider == "openai":
                panel = cls._build_openai_panel(effective_cfg)
            elif provider == "gemini":
                panel = cls._build_gemini_panel(effective_cfg, 0, 0)
            elif provider == "glm":
                panel = cls._build_glm_panel(effective_cfg, 0, 0)
            else:
                return {"success": False, "message": "不支持的 provider"}

            return {"success": True, "message": "草稿验证成功（尚未保存）", "panel": panel}
        except Exception as err:
            return {"success": False, "message": cls._safe_error(err)}
