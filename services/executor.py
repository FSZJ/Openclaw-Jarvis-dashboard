"""
Operation executor service - performs actions on OpenClaw system
"""
import subprocess
import shutil
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from config import OPENCLAW_DIR, WORKSPACE_DIR
from models import ActionResult, BackupInfo


class OperationExecutor:
    """Executes operations on OpenClaw system"""

    @staticmethod
    def _resolve_remindctl_cmd(cmd: List[str]) -> List[str]:
        """Resolve remindctl binary path for non-interactive service environments."""
        if not cmd or cmd[0] != "remindctl":
            return cmd

        candidates = [
            shutil.which("remindctl"),
            "/opt/homebrew/bin/remindctl",
            "/usr/local/bin/remindctl",
            "/usr/bin/remindctl",
        ]
        for path in candidates:
            if path and os.path.exists(path):
                resolved = list(cmd)
                resolved[0] = path
                return resolved
        return cmd

    def restart_gateway(self) -> ActionResult:
        """Restart the OpenClaw Gateway"""
        try:
            result = subprocess.run(
                ["openclaw", "gateway", "restart"],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                return ActionResult(
                    success=True,
                    message="Gateway restart command sent successfully",
                    data={"output": result.stdout}
                )
            else:
                return ActionResult(
                    success=False,
                    message=f"Failed to restart Gateway: {result.stderr}",
                    data={"error": result.stderr}
                )
        except subprocess.TimeoutExpired:
            return ActionResult(
                success=False,
                message="Gateway restart timed out"
            )
        except FileNotFoundError:
            return ActionResult(
                success=False,
                message="OpenClaw CLI not found. Make sure openclaw is installed."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Error restarting Gateway: {str(e)}"
            )

    def stop_gateway(self) -> ActionResult:
        """Stop the OpenClaw Gateway"""
        try:
            result = subprocess.run(
                ["pkill", "-f", "openclaw-gateway"],
                capture_output=True, text=True
            )

            return ActionResult(
                success=True,
                message="Gateway stop command sent"
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Error stopping Gateway: {str(e)}"
            )

    def start_gateway(self) -> ActionResult:
        """Start the OpenClaw Gateway"""
        try:
            result = subprocess.run(
                ["openclaw", "gateway", "start"],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                return ActionResult(
                    success=True,
                    message="Gateway start command sent successfully"
                )
            else:
                return ActionResult(
                    success=False,
                    message=f"Failed to start Gateway: {result.stderr}"
                )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Error starting Gateway: {str(e)}"
            )

    def create_backup(self) -> ActionResult:
        """Create a backup of OpenClaw configuration"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"openclaw_backup_{timestamp}"
            backup_dir = OPENCLAW_DIR.parent / "backups" / backup_name

            # Create backup directory
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Copy configuration files
            backup_files = [
                "openclaw.json",
                "node.json",
                "agents/main/agent/models.json"
            ]

            for file in backup_files:
                src = OPENCLAW_DIR / file
                if src.exists():
                    dst = backup_dir / file
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

            # Get backup info
            backup_info = BackupInfo(
                filename=backup_name,
                size=int(sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())),
                created_at=datetime.now().isoformat()
            )

            return ActionResult(
                success=True,
                message=f"Backup created: {backup_name}",
                data=backup_info.dict()
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Error creating backup: {str(e)}"
            )

    def clear_logs(self) -> ActionResult:
        """Clear log files"""
        try:
            log_dir = OPENCLAW_DIR / "logs"
            if not log_dir.exists():
                return ActionResult(success=True, message="No logs to clear")

            for log_file in log_dir.glob("*.log"):
                with open(log_file, 'w') as f:
                    f.write("")

            return ActionResult(
                success=True,
                message="Log files cleared"
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Error clearing logs: {str(e)}"
            )

    def get_recent_logs(self, lines: int = 100) -> ActionResult:
        """Get recent log content"""
        try:
            log_file = OPENCLAW_DIR / "logs" / "gateway.log"
            if not log_file.exists():
                return ActionResult(
                    success=False,
                    message="Gateway log not found"
                )

            with open(log_file) as f:
                all_lines = f.readlines()
                recent = all_lines[-lines:] if len(all_lines) > lines else all_lines

            return ActionResult(
                success=True,
                message="Recent logs retrieved",
                data={"logs": "".join(recent)}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Error reading logs: {str(e)}"
            )

    def send_message(self, message: str) -> ActionResult:
        """Send a test message through the Gateway"""
        try:
            result = subprocess.run(
                ["curl", "-s", "-X", "POST",
                 "http://localhost:7777/api/message",
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps({"message": message, "stream": "false"})],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                return ActionResult(
                    success=True,
                    message="Message sent successfully",
                    data={"response": result.stdout}
                )
            else:
                return ActionResult(
                    success=False,
                    message=f"Failed to send message: {result.stderr}"
                )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Error sending message: {str(e)}"
            )

    def list_backups(self) -> ActionResult:
        """List available backups"""
        try:
            backup_parent = OPENCLAW_DIR.parent / "backups"

            if not backup_parent.exists():
                return ActionResult(
                    success=True,
                    message="No backups directory",
                    data={"backups": []}
                )

            backups = []
            for backup_dir in backup_parent.iterdir():
                if backup_dir.is_dir():
                    size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
                    backups.append({
                        "filename": backup_dir.name,
                        "size": size,
                        "created_at": datetime.fromtimestamp(backup_dir.stat().st_ctime).isoformat()
                    })

            return ActionResult(
                success=True,
                message="Backups retrieved",
                data={"backups": backups}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Error listing backups: {str(e)}"
            )

    def create_todo(self, title: str, list_name: str = "默认列表", due_date: Optional[str] = None) -> ActionResult:
        """Create a todo item via remindctl."""
        title = (title or "").strip()
        list_name = (list_name or "贾维斯的待办").strip()
        if not title:
            return ActionResult(success=False, message="任务标题不能为空")
        cmd = ["remindctl", "add", "--title", title, "--list", list_name]
        if due_date:
            cmd.extend(["--due", due_date])
        result = self._run_remindctl(cmd, timeout=10)
        if not result.success:
            return result

        return ActionResult(
            success=True,
            message="任务已创建",
            data={"title": title, "list_name": list_name, "due_date": due_date}
        )

    def list_todos(self, list_name: str = "贾维斯的待办") -> ActionResult:
        """List todo items from Apple Reminders."""
        primary = self._run_remindctl(["remindctl", "list", list_name, "--json"], timeout=10)
        if not primary.success:
            primary = self._run_remindctl(["remindctl", "today", "--json"], timeout=10)
        if not primary.success:
            return primary

        try:
            payload = json.loads(primary.data.get("stdout", "[]"))
            todos = self._extract_todos_from_payload(payload, default_list=list_name)
            return ActionResult(success=True, message="todos retrieved", data={"todos": todos})
        except Exception as e:
            return ActionResult(success=False, message=f"解析提醒列表失败: {str(e)}")

    def list_completed_todos(self, list_name: str = "贾维斯的待办", limit: int = 30) -> ActionResult:
        """List completed reminder items."""
        result = self._run_remindctl(["remindctl", "completed", "--json"], timeout=10)
        if not result.success:
            return result
        try:
            payload = json.loads(result.data.get("stdout", "[]"))
            tasks = self._extract_todos_from_payload(payload, default_list=list_name, include_completed=True)
            tasks = [t for t in tasks if t.get("completed")]
            tasks = sorted(tasks, key=lambda x: str(x.get("completed_at") or ""), reverse=True)
            return ActionResult(success=True, message="history retrieved", data={"tasks": tasks[:limit]})
        except Exception as e:
            return ActionResult(success=False, message=f"解析历史任务失败: {str(e)}")

    def complete_todo(self, task_id: str) -> ActionResult:
        """Complete a reminder by id."""
        if not task_id:
            return ActionResult(success=False, message="任务ID不能为空")
        return self._run_remindctl(["remindctl", "complete", str(task_id)], timeout=10)

    def _run_remindctl(self, cmd: List[str], timeout: int = 8) -> ActionResult:
        cmd = self._resolve_remindctl_cmd(cmd)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            return ActionResult(success=False, message="未检测到 remindctl，无法读取 Apple 提醒。")
        except Exception as e:
            return ActionResult(success=False, message=f"执行 remindctl 失败: {str(e)}")

        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            detail = stderr or stdout or "unknown error"
            return ActionResult(success=False, message=f"remindctl 失败: {detail}")

        return ActionResult(
            success=True,
            message="ok",
            data={"stdout": result.stdout, "stderr": result.stderr}
        )

    def _extract_todos_from_payload(self, payload: Any, default_list: str, include_completed: bool = False) -> List[Dict[str, Any]]:
        tasks: List[Dict[str, Any]] = []
        seen = set()

        def walk(node: Any, list_name: str):
            if isinstance(node, list):
                for item in node:
                    walk(item, list_name)
                return

            if not isinstance(node, dict):
                return

            nested_list = str(node.get("list") or node.get("list_name") or node.get("name") or list_name or default_list)
            keys = ("items", "tasks", "todos", "reminders", "data")
            for key in keys:
                if key in node and isinstance(node[key], (list, dict)):
                    walk(node[key], nested_list)

            title = node.get("title") or node.get("name") or node.get("text")
            if not isinstance(title, str) or not title.strip():
                return
            task_id = str(node.get("id") or node.get("uuid") or "")
            if not task_id:
                task_id = f"tmp-{title.strip()}"
            if task_id in seen:
                return
            seen.add(task_id)

            status = str(node.get("status") or "").lower()
            completed = bool(
                node.get("completed")
                or node.get("isCompleted")
                or status in {"completed", "done", "closed"}
                or node.get("completed_at")
                or node.get("completionDate")
            )
            if completed and not include_completed:
                return

            due = node.get("due") or node.get("due_date") or node.get("dueDate")
            completed_at = node.get("completed_at") or node.get("completionDate")

            tasks.append({
                "id": task_id,
                "title": title.strip(),
                "due_date": due,
                "completed": completed,
                "completed_at": completed_at,
                "list_name": nested_list or default_list,
                "source": "apple_reminders",
            })

        walk(payload, default_list)
        return tasks
