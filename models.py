"""
Data models for OpenClaw Dashboard
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============== Task Models ==============

class TodoTask(BaseModel):
    """待办任务"""
    id: str
    title: str
    due_date: Optional[str] = None
    completed: bool = False
    list_name: str = "默认列表"

class CompletedTask(BaseModel):
    """已完成任务"""
    id: str
    title: str
    completed_at: str
    list_name: str = "默认列表"

class TodoCreateRequest(BaseModel):
    """创建待办任务请求"""
    title: str
    list_name: Optional[str] = "默认列表"
    due_date: Optional[str] = None


class IntegrationsUpdateRequest(BaseModel):
    """更新模型集成配置请求"""
    providers: Dict[str, Dict[str, Any]]

# ============== User Models ==============

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    must_change_password: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# ============== Status Models ==============

class GatewayStatus(BaseModel):
    running: bool
    pid: Optional[int] = None
    uptime: Optional[str] = None

class SystemHealth(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    gateway: GatewayStatus

class NodeInfo(BaseModel):
    node_id: str
    display_name: str
    gateway_host: str
    gateway_port: int

# ============== Agent Models ==============

class ModelInfo(BaseModel):
    id: str
    name: str
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None

class ProviderInfo(BaseModel):
    name: str
    base_url: str
    models: List[ModelInfo]

class AgentConfig(BaseModel):
    provider: str
    model: str
    providers: Dict[str, ProviderInfo]

class SubAgentRun(BaseModel):
    run_id: str
    agent_name: str
    status: str  # running, completed, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error: Optional[str] = None

class AgentStatus(BaseModel):
    main_agent: AgentConfig
    subagents_running: int
    subagent_runs: List[SubAgentRun] = []

# ============== Channel Models ==============

class TelegramConfig(BaseModel):
    enabled: bool
    bot_token: Optional[str] = None
    stream_mode: Optional[str] = None

class IMessageConfig(BaseModel):
    enabled: bool

class ChannelStatus(BaseModel):
    telegram: TelegramConfig
    imessage: IMessageConfig

# ============== Log Models ==============

class LogInfo(BaseModel):
    file: str
    size: int
    last_modified: Optional[str] = None
    error_count: int = 0
    last_error: Optional[str] = None

class MinimaxModelQuota(BaseModel):
    model_name: Optional[str] = None
    total: Optional[int] = None
    used: Optional[int] = None
    remaining: Optional[int] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    remains_time: Optional[int] = None

class MinimaxQuota(BaseModel):
    total: Optional[int] = None
    used: Optional[int] = None
    remaining: Optional[int] = None
    unit: Optional[str] = None
    window_end_time: Optional[int] = None
    models: List[MinimaxModelQuota] = Field(default_factory=list)

# ============== Action Models ==============

class ActionResult(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class BackupInfo(BaseModel):
    filename: str
    size: int
    created_at: str

# ============== Full Dashboard Response ==============

class DashboardStatus(BaseModel):
    timestamp: datetime
    node: NodeInfo
    system: SystemHealth
    agents: AgentStatus
    channels: ChannelStatus
    logs: List[LogInfo]
    minimax: Optional[MinimaxQuota] = None
