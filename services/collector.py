"""
Status collector service - gathers system status from OpenClaw
"""
import subprocess
import psutil
import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from config import OPENCLAW_DIR, WORKSPACE_DIR, STATUS_CACHE_TTL, MINIMAX_API_KEY, MINIMAX_GROUP_ID, MINIMAX_QUOTA_URL, MINIMAX_USAGE_IS_REMAINING
from services.task_store import TaskStore
from services.usage_service import UsageService
from models import (
    GatewayStatus, SystemHealth, NodeInfo, AgentConfig,
    AgentStatus, ChannelStatus, LogInfo, ProviderInfo, ModelInfo,
    SubAgentRun, MinimaxQuota
)
from urllib.request import Request, urlopen
from urllib.error import URLError


class StatusCollector:
    """Collects status information from OpenClaw system"""
    _status_cache: Optional[Dict[str, Any]] = None
    _status_cache_ts: float = 0.0
    _todos_cache: Optional[List[Dict[str, Any]]] = None
    _todos_cache_ts: float = 0.0
    _completed_cache: Optional[List[Dict[str, Any]]] = None
    _completed_cache_ts: float = 0.0

    @classmethod
    def invalidate_todos_cache(cls):
        """Clear todos cache after mutations."""
        cls._todos_cache = None
        cls._todos_cache_ts = 0.0
        cls._completed_cache = None
        cls._completed_cache_ts = 0.0
        cls._status_cache = None
        cls._status_cache_ts = 0.0

    def get_gateway_status(self) -> GatewayStatus:
        """Check if Gateway process is running"""
        try:
            # Find openclaw-gateway process
            result = subprocess.run(
                ["pgrep", "-f", "openclaw-gateway"],
                capture_output=True, text=True
            )
            pids = result.stdout.strip().split('\n') if result.stdout.strip() else []

            if pids and pids[0]:
                pid = int(pids[0])
                # Check if process is actually running
                try:
                    proc = psutil.Process(pid)
                    uptime_seconds = (datetime.now() - datetime.fromtimestamp(proc.create_time()))
                    uptime_str = str(uptime_seconds).split('.')[0]  # Remove microseconds
                    return GatewayStatus(running=True, pid=pid, uptime=uptime_str)
                except psutil.NoSuchProcess:
                    pass

            return GatewayStatus(running=False)
        except Exception as e:
            return GatewayStatus(running=False)

    def get_system_health(self) -> SystemHealth:
        """Get system resource usage"""
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        gateway = self.get_gateway_status()

        return SystemHealth(
            cpu_percent=cpu,
            memory_percent=memory.percent,
            disk_usage_percent=disk.percent,
            gateway=gateway
        )

    def get_node_info(self) -> Optional[NodeInfo]:
        """Read node configuration"""
        node_file = OPENCLAW_DIR / "node.json"
        if not node_file.exists():
            return None

        try:
            with open(node_file) as f:
                data = json.load(f)
            return NodeInfo(
                node_id=data.get("nodeId", ""),
                display_name=data.get("displayName", ""),
                gateway_host=data.get("gateway", {}).get("host", ""),
                gateway_port=data.get("gateway", {}).get("port", 0)
            )
        except Exception:
            return None

    def get_agent_config(self) -> AgentConfig:
        """Read agent configuration"""
        models_file = OPENCLAW_DIR / "agents" / "main" / "agent" / "models.json"
        providers = {}

        if models_file.exists():
            try:
                with open(models_file) as f:
                    data = json.load(f)

                for provider_name, provider_data in data.get("providers", {}).items():
                    models = []
                    for model in provider_data.get("models", []):
                        models.append(ModelInfo(
                            id=model.get("id", ""),
                            name=model.get("name", ""),
                            context_window=model.get("contextWindow"),
                            max_tokens=model.get("maxTokens")
                        ))
                    providers[provider_name] = ProviderInfo(
                        name=provider_name,
                        base_url=provider_data.get("baseUrl", ""),
                        models=models
                    )
            except Exception:
                pass

        # Get default model from main config
        openclaw_file = OPENCLAW_DIR / "openclaw.json"
        default_model = "unknown"
        if openclaw_file.exists():
            try:
                with open(openclaw_file) as f:
                    data = json.load(f)
                default_model = data.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "unknown")
            except Exception:
                pass

        return AgentConfig(
            provider=list(providers.keys())[0] if providers else "unknown",
            model=default_model,
            providers=providers
        )

    def get_subagent_runs(self) -> List[SubAgentRun]:
        """Read subagent run history"""
        runs_file = OPENCLAW_DIR / "subagents" / "runs.json"
        runs = []

        if runs_file.exists():
            try:
                with open(runs_file) as f:
                    data = json.load(f)

                for run_id, run_data in data.get("runs", {}).items():
                    runs.append(SubAgentRun(
                        run_id=run_id,
                        agent_name=run_data.get("agentName", ""),
                        status=run_data.get("status", "unknown"),
                        start_time=run_data.get("startTime"),
                        end_time=run_data.get("endTime"),
                        error=run_data.get("error")
                    ))
            except Exception:
                pass

        return runs

    def get_agent_status(self) -> AgentStatus:
        """Get complete agent status"""
        config = self.get_agent_config()
        runs = self.get_subagent_runs()
        running_count = len([r for r in runs if r.status == "running"])

        return AgentStatus(
            main_agent=config,
            subagents_running=running_count,
            subagent_runs=runs
        )

    def get_channel_status(self) -> ChannelStatus:
        """Read channel configuration"""
        config_file = OPENCLAW_DIR / "openclaw.json"
        telegram_enabled = False
        telegram_token = None
        telegram_stream = None
        imessage_enabled = False

        if config_file.exists():
            try:
                with open(config_file) as f:
                    data = json.load(f)

                channels = data.get("channels", {})
                telegram_config = channels.get("telegram", {})
                telegram_enabled = telegram_config.get("enabled", False)
                telegram_token = telegram_config.get("botToken")
                telegram_stream = telegram_config.get("streamMode")

                imessage_enabled = channels.get("imessage", {}).get("enabled", False)
            except Exception:
                pass

        return ChannelStatus(
            telegram={
                "enabled": telegram_enabled,
                "bot_token": telegram_token,
                "stream_mode": telegram_stream
            },
            imessage={"enabled": imessage_enabled}
        )

    def get_log_info(self) -> List[LogInfo]:
        """Get log file information"""
        log_dir = OPENCLAW_DIR / "logs"
        logs = []

        if log_dir.exists():
            log_files = ["gateway.log", "gateway.err.log", "node.log", "node.err.log"]
            for log_file in log_files:
                log_path = log_dir / log_file
                if log_path.exists():
                    try:
                        stat = log_path.stat()
                        # Count error lines
                        error_count = 0
                        last_error = None
                        with open(log_path) as f:
                            for line in f:
                                if "error" in line.lower() or "exception" in line.lower():
                                    error_count += 1
                                    last_error = line.strip()

                        logs.append(LogInfo(
                            file=log_file,
                            size=stat.st_size,
                            last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            error_count=error_count,
                            last_error=last_error[:200] if last_error else None
                        ))
                    except Exception:
                        pass

        return logs

    def get_minimax_quota(self) -> Optional[MinimaxQuota]:
        """Fetch Minimax quota if endpoint is configured"""
        if not MINIMAX_API_KEY or not MINIMAX_QUOTA_URL:
            return None

        url = MINIMAX_QUOTA_URL
        if "{group_id}" in url and MINIMAX_GROUP_ID:
            url = url.format(group_id=MINIMAX_GROUP_ID)

        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=5) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (URLError, ValueError, TimeoutError):
            return None

        data = payload.get("data", payload) if isinstance(payload, dict) else {}

        # Coding plan model remains format
        model_remains = data.get("model_remains")
        if isinstance(model_remains, list) and model_remains:
            models = []
            total_sum = 0
            used_sum = 0
            remaining_sum = 0
            window_end_time = None

            for item in model_remains:
                try:
                    total = int(item.get("current_interval_total_count") or 0)
                    usage_raw = int(item.get("current_interval_usage_count") or 0)
                except (TypeError, ValueError):
                    total = 0
                    usage_raw = 0

                if MINIMAX_USAGE_IS_REMAINING:
                    remaining = max(usage_raw, 0)
                    used = max(total - remaining, 0)
                else:
                    used = max(usage_raw, 0)
                    remaining = max(total - used, 0)
                total_sum += total
                used_sum += used
                remaining_sum += remaining

                end_time = item.get("end_time")
                if window_end_time is None and end_time is not None:
                    window_end_time = end_time

                models.append({
                    "model_name": item.get("model_name"),
                    "total": total,
                    "used": used,
                    "remaining": remaining,
                    "start_time": item.get("start_time"),
                    "end_time": end_time,
                    "remains_time": item.get("remains_time")
                })

            return MinimaxQuota(
                total=total_sum,
                used=used_sum,
                remaining=remaining_sum,
                unit="count",
                window_end_time=window_end_time,
                models=models
            )

        remaining = data.get("remaining") or data.get("balance") or data.get("left") or data.get("remain")
        total = data.get("total") or data.get("quota") or data.get("limit")
        unit = data.get("unit") or data.get("currency")

        if remaining is None and total is None:
            return None

        used = None
        if total is not None and remaining is not None:
            try:
                used = max(float(total) - float(remaining), 0)
            except (TypeError, ValueError):
                used = None

        return MinimaxQuota(total=total, used=used, remaining=remaining, unit=unit)

    def get_full_status(self, light: bool = False) -> Dict[str, Any]:
        """Get complete dashboard status"""
        now = time.time()
        if self._status_cache and (now - self._status_cache_ts) < STATUS_CACHE_TTL:
            return self._status_cache

        minimax = None if light else self.get_minimax_quota()
        agents = self.get_agent_status()
        running_tasks = len([r for r in agents.subagent_runs if r.status == "running"])
        usage_panels = [] if light else UsageService.get_usage_panels(
            running_tasks=running_tasks,
            running_agents=agents.subagents_running
        )
        status = {
            "timestamp": datetime.now().isoformat(),
            "node": self.get_node_info().dict() if self.get_node_info() else None,
            "system": self.get_system_health().dict(),
            "agents": agents.dict(),
            "channels": self.get_channel_status().dict(),
            "logs": [] if light else [log.dict() for log in self.get_log_info()],
            "todos": [] if light else self.get_todos(),
            "completed_tasks": [] if light else self.get_completed_tasks(),
            "minimax": minimax.dict() if minimax else None,
            "usage_panels": usage_panels,
        }
        self._status_cache = status
        self._status_cache_ts = now
        return status

    def get_todos(self) -> List[Dict[str, Any]]:
        """Get pending todos from local store."""
        now = time.time()
        if self._todos_cache and (now - self._todos_cache_ts) < max(STATUS_CACHE_TTL, 30):
            return self._todos_cache

        todos = TaskStore.list_todos()
        self._todos_cache = todos
        self._todos_cache_ts = now
        return todos

    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """Get completed tasks from local store."""
        now = time.time()
        if self._completed_cache and (now - self._completed_cache_ts) < max(STATUS_CACHE_TTL, 30):
            return self._completed_cache

        tasks = TaskStore.list_completed(limit=30)
        self._completed_cache = tasks
        self._completed_cache_ts = now
        return tasks
