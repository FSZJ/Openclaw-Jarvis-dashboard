#!/usr/bin/env python3
"""
Manual sync tool:
Import Apple Reminders tasks into OpenClaw local task store.
Run this in a terminal session that already has remindctl permissions.
"""
import sys
from pathlib import Path

# Ensure project root is importable when running as a plain script path.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.executor import OperationExecutor
from services.task_store import TaskStore


def main():
    ex = OperationExecutor()
    todos_result = ex.list_todos("贾维斯的待办")
    done_result = ex.list_completed_todos(limit=500)

    if not todos_result.success and not done_result.success:
        print(f"sync failed: {todos_result.message}")
        return 1

    todo_count = 0
    done_count = 0

    if todos_result.success:
        todos = todos_result.data.get("todos", []) if todos_result.data else []
        TaskStore.sync_apple_todos(todos)
        todo_count = len(todos)

    if done_result.success:
        tasks = done_result.data.get("tasks", []) if done_result.data else []
        TaskStore.sync_apple_completed(tasks)
        done_count = len(tasks)

    print(f"sync ok: todos={todo_count}, completed={done_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
