"""
Local task storage for dashboard todos/history.
"""
import json
import re
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from config import OPENCLAW_DIR


TASKS_FILE = OPENCLAW_DIR / "dashboard_tasks.json"


class TaskStore:
    """File-backed task store."""
    _lock = Lock()

    @classmethod
    def _now_iso(cls) -> str:
        return datetime.utcnow().isoformat()

    @classmethod
    def _default_payload(cls) -> Dict[str, Any]:
        return {
            "version": 1,
            "updated_at": cls._now_iso(),
            "bootstrap_done": False,
            "bootstrap_sources": [],
            "todos": [],
            "completed": [],
        }

    @classmethod
    def _ensure_file(cls):
        if TASKS_FILE.exists():
            return
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        TASKS_FILE.write_text(json.dumps(cls._default_payload(), ensure_ascii=False, indent=2))

    @classmethod
    def _load(cls) -> Dict[str, Any]:
        cls._ensure_file()
        try:
            payload = json.loads(TASKS_FILE.read_text() or "{}")
        except Exception:
            payload = cls._default_payload()
        if not isinstance(payload, dict):
            payload = cls._default_payload()
        payload.setdefault("todos", [])
        payload.setdefault("completed", [])
        payload.setdefault("updated_at", cls._now_iso())
        payload.setdefault("bootstrap_done", False)
        payload.setdefault("bootstrap_sources", [])

        # Best-effort one-time bootstrap for existing reminders/tasks.
        if (not payload.get("bootstrap_done")) and not payload.get("todos") and not payload.get("completed"):
            seeded, source = cls._bootstrap_seed_tasks()
            if seeded:
                payload["todos"] = seeded
                if source:
                    payload["bootstrap_sources"] = [source]
            payload["bootstrap_done"] = True
            cls._save(payload)
        return payload

    @classmethod
    def _save(cls, payload: Dict[str, Any]):
        payload["updated_at"] = cls._now_iso()
        TASKS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    @classmethod
    def _normalize_task(cls, item: Dict[str, Any], source: str, completed: bool) -> Dict[str, Any]:
        task_id = str(item.get("id") or item.get("uuid") or uuid4().hex[:12])
        return {
            "id": task_id,
            "title": str(item.get("title") or "").strip(),
            "due_date": item.get("due_date"),
            "completed": completed,
            "completed_at": item.get("completed_at"),
            "list_name": item.get("list_name") or "默认列表",
            "created_at": item.get("created_at") or cls._now_iso(),
            "source": source,
        }

    @classmethod
    def sync_apple_todos(cls, todos: List[Dict[str, Any]]) -> Dict[str, int]:
        """Replace apple-sourced pending todos with latest snapshot."""
        with cls._lock:
            payload = cls._load()
            pending = payload.get("todos") or []
            local_pending = [
                t for t in pending
                if isinstance(t, dict)
                and t.get("source") not in {"apple_reminders", "memory_todos_md"}
            ]

            new_apple = []
            for item in todos or []:
                if not isinstance(item, dict):
                    continue
                if item.get("completed"):
                    continue
                normalized = cls._normalize_task(item, "apple_reminders", completed=False)
                if normalized["title"]:
                    new_apple.append(normalized)

            payload["todos"] = local_pending + new_apple
            cls._save(payload)
            return {"local_pending": len(local_pending), "apple_pending": len(new_apple)}

    @classmethod
    def sync_apple_completed(cls, completed: List[Dict[str, Any]]) -> Dict[str, int]:
        """Replace apple-sourced completed tasks with latest snapshot."""
        with cls._lock:
            payload = cls._load()
            done = payload.get("completed") or []
            local_done = [t for t in done if isinstance(t, dict) and t.get("source") != "apple_reminders"]

            apple_done = []
            completed_ids = set()
            for item in completed or []:
                if not isinstance(item, dict):
                    continue
                normalized = cls._normalize_task(item, "apple_reminders", completed=True)
                if normalized["title"]:
                    if not normalized.get("completed_at"):
                        normalized["completed_at"] = cls._now_iso()
                    apple_done.append(normalized)
                    completed_ids.add(normalized["id"])

            # Ensure pending list does not keep completed apple items.
            pending = payload.get("todos") or []
            payload["todos"] = [
                t for t in pending
                if not (isinstance(t, dict) and t.get("source") == "apple_reminders" and t.get("id") in completed_ids)
            ]
            payload["completed"] = local_done + apple_done
            cls._save(payload)
            return {"local_completed": len(local_done), "apple_completed": len(apple_done)}

    @classmethod
    def _bootstrap_seed_tasks(cls) -> tuple[List[Dict[str, Any]], Optional[str]]:
        seeded = cls._seed_from_markdown()
        if seeded:
            return seeded, "memory_todos_md"
        return [], None

    @classmethod
    def _seed_from_markdown(cls) -> List[Dict[str, Any]]:
        md_file = OPENCLAW_DIR / "workspace" / "memory" / "todos.md"
        if not md_file.exists():
            return []

        pattern = re.compile(r"^\s*-\s*\[\s\]\s*(.+?)\s*$")
        entries: List[Dict[str, Any]] = []
        seen_titles = set()

        for raw in md_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = pattern.match(raw)
            if not match:
                continue
            title = match.group(1).strip()
            if not title:
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)
            entries.append({
                "id": uuid4().hex[:12],
                "title": title,
                "due_date": None,
                "completed": False,
                "list_name": "默认列表",
                "created_at": cls._now_iso(),
                "source": "memory_todos_md",
            })

        return entries[:200]

    @classmethod
    def list_todos(cls) -> List[Dict[str, Any]]:
        with cls._lock:
            payload = cls._load()
            todos = payload.get("todos") or []
            todos = [t for t in todos if isinstance(t, dict)]
            todos.sort(key=lambda t: t.get("created_at") or "", reverse=True)
            return todos

    @classmethod
    def list_completed(cls, limit: Optional[int] = 20) -> List[Dict[str, Any]]:
        with cls._lock:
            payload = cls._load()
            completed = payload.get("completed") or []
            completed = [t for t in completed if isinstance(t, dict)]
            completed.sort(key=lambda t: t.get("completed_at") or "", reverse=True)
            if limit is not None:
                return completed[:limit]
            return completed

    @classmethod
    def create_todo(cls, title: str, list_name: str = "默认列表", due_date: Optional[str] = None) -> Dict[str, Any]:
        title = (title or "").strip()
        if not title:
            raise ValueError("任务标题不能为空")

        with cls._lock:
            payload = cls._load()
            task = {
                "id": uuid4().hex[:12],
                "title": title,
                "due_date": due_date,
                "completed": False,
                "list_name": list_name or "默认列表",
                "created_at": cls._now_iso(),
                "source": "local",
            }
            payload["todos"] = [task] + (payload.get("todos") or [])
            cls._save(payload)
            return task

    @classmethod
    def complete_todo(cls, task_id: str) -> Optional[Dict[str, Any]]:
        with cls._lock:
            payload = cls._load()
            todos = payload.get("todos") or []
            picked = None
            remain = []
            for item in todos:
                if not picked and item.get("id") == task_id:
                    picked = item
                else:
                    remain.append(item)
            if not picked:
                return None
            picked["completed"] = True
            picked["completed_at"] = cls._now_iso()
            payload["todos"] = remain
            payload["completed"] = [picked] + (payload.get("completed") or [])
            cls._save(payload)
            return picked

    @classmethod
    def delete_todo(cls, task_id: str) -> bool:
        """Delete a pending todo by id."""
        with cls._lock:
            payload = cls._load()
            todos = payload.get("todos") or []
            remain = [t for t in todos if not (isinstance(t, dict) and t.get("id") == task_id)]
            changed = len(remain) != len(todos)
            if changed:
                payload["todos"] = remain
                cls._save(payload)
            return changed

    @classmethod
    def reopen_task(cls, task_id: str) -> Optional[Dict[str, Any]]:
        with cls._lock:
            payload = cls._load()
            completed = payload.get("completed") or []
            picked = None
            remain = []
            for item in completed:
                if not picked and item.get("id") == task_id:
                    picked = item
                else:
                    remain.append(item)
            if not picked:
                return None
            picked["completed"] = False
            picked.pop("completed_at", None)
            payload["completed"] = remain
            payload["todos"] = [picked] + (payload.get("todos") or [])
            cls._save(payload)
            return picked
