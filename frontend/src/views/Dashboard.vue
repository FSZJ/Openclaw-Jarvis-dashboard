<template>
  <div class="dashboard-page min-h-[100dvh] overflow-x-hidden">
    <header class="relative z-40 h-16 bg-gray-900/80 backdrop-blur border-b border-gray-800">
      <div class="max-w-full mx-auto px-4 h-full flex items-center justify-between">
        <div class="flex items-center gap-3">
          <h1 class="text-lg font-bold text-openclaw-300">OpenClaw Jarvis</h1>
          <span class="neon-pill">Ops Copilot</span>
        </div>

        <div class="flex items-center gap-3 relative">
          <div class="neon-pill" :class="jarvisMoodClass">
            <span>{{ jarvisFace }}</span>
            <span>{{ jarvisMoodLabel }}</span>
          </div>
          <div ref="alertsWrap" class="relative">
            <button
              @click.stop="toggleAlerts"
              class="p-2 text-gray-300 hover:text-white transition-colors rounded-lg hover:bg-gray-800"
              aria-label="alerts"
              :aria-expanded="showAlerts ? 'true' : 'false'"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0a3 3 0 11-6 0h6z"
                />
              </svg>
              <span v-if="alertCount > 0" class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full px-1.5">
                {{ alertCount }}
              </span>
            </button>
            <div v-if="showAlerts" class="absolute right-0 mt-2 w-[min(22rem,92vw)] card glass z-[90]" @click.stop>
              <div class="card-header">
                <h3 class="card-title">异常提醒</h3>
                <button class="text-gray-300 hover:text-white text-xs" @click="closeAlerts">关闭</button>
              </div>
              <div class="space-y-2 max-h-56 overflow-y-auto">
                <div v-if="alertItems.length === 0" class="text-gray-500 text-center py-3">
                  暂无异常
                </div>
                <div v-for="item in alertItems" :key="item.key" class="p-2 rounded bg-gray-700/40">
                  <div class="flex justify-between items-center">
                    <span class="font-medium">{{ item.title }}</span>
                    <span class="text-red-300" v-if="item.count">x{{ item.count }}</span>
                  </div>
                  <p class="text-gray-300 mt-1">{{ item.detail }}</p>
                </div>
              </div>
            </div>
          </div>
          <button
            @click="logout"
            class="text-gray-300 hover:text-white px-3 py-1 rounded-lg hover:bg-gray-800"
          >
            退出
          </button>
        </div>
      </div>
    </header>

    <main class="dashboard-main max-w-full mx-auto px-4 py-3">
      <div v-if="dashboardStore.error" class="mb-2 p-3 bg-red-900/50 border border-red-700 rounded-lg">
        <p class="text-red-300">{{ dashboardStore.error }}</p>
      </div>

      <div v-if="!dashboardStore.status && dashboardStore.loading" class="min-h-[40vh] flex justify-center items-center">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-openclaw-500"></div>
      </div>

      <div v-else-if="dashboardStore.status" class="dashboard-shell">
        <section class="dashboard-grid">
          <div class="dashboard-primary">
            <div class="card glass jarvis hero-panel relative overflow-hidden p-4 xl:p-5 shrink-0">
              <div class="scan-line"></div>
              <div class="flex items-center gap-4 xl:gap-5 h-full">
                <div class="relative shrink-0">
                  <JarvisAvatar :mood="jarvisState" />
                  <span class="status-chip absolute -bottom-4 left-1/2 -translate-x-1/2" :class="gatewayStatusColor">
                    {{ dashboardStore.status.system?.gateway?.running ? '运行中' : '已停止' }}
                  </span>
                </div>
                <div class="w-full min-w-0 flex flex-col gap-2 xl:gap-3">
                  <div class="space-y-1.5">
                    <p class="uppercase tracking-[0.35em] text-openclaw-300">Jarvis Online</p>
                    <h2 class="text-3xl font-bold leading-tight">你的全息助理，随时待命</h2>
                    <p class="text-gray-300">{{ jarvisMessage }}</p>
                  </div>
                  <div class="hero-status-grid mt-1">
                    <div v-for="group in heroGroups" :key="group.key" class="hero-status-group">
                      <div class="hero-status-group-title">
                        <span>{{ group.icon }}</span>
                        <span>{{ group.title }}</span>
                      </div>
                      <div class="hero-status-items no-wrap">
                        <div
                          v-for="item in group.items"
                          :key="item.key"
                          class="hero-status-pill"
                          :class="`tone-${item.tone}`"
                        >
                          <span class="pill-icon">{{ item.icon }}</span>
                          <span class="pill-label">{{ item.label }}</span>
                          <span class="pill-value">{{ item.value }}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>
              </div>
            </div>

            <div class="card glass compact-panel shrink-0">
              <div class="card-header items-center !mb-3 !pb-2">
                <h3 class="card-title">快捷操作</h3>
              </div>
              <div class="hero-control-grid">
                <button class="action-tile danger hero-action" :disabled="actionLoading" @click="confirmRestart">
                  <div class="action-tile-content">
                    <span class="action-icon">🔄</span>
                    <span>重启</span>
                    <small class="action-subtitle tone-danger">短暂中断</small>
                  </div>
                </button>
                <button class="action-tile primary hero-action" :disabled="actionLoading" @click="createBackup">
                  <div class="action-tile-content">
                    <span class="action-icon">💾</span>
                    <span>备份</span>
                    <small class="action-subtitle tone-primary">全量配置</small>
                  </div>
                </button>
                <button class="action-tile neutral hero-action" :disabled="actionLoading" @click="clearLogs">
                  <div class="action-tile-content">
                    <span class="action-icon">🧹</span>
                    <span>清日志</span>
                    <small class="action-subtitle tone-neutral">释放存储</small>
                  </div>
                </button>
                <button class="action-tile neutral hero-action" :disabled="actionLoading" @click="refresh">
                  <div class="action-tile-content">
                    <span class="action-icon">🔃</span>
                    <span>刷新</span>
                    <small class="action-subtitle tone-neutral">即时拉取</small>
                  </div>
                </button>
              </div>
              <div v-if="actionLoading" class="mt-2">
                <div class="progress-bar">
                  <div class="progress-bar-inner indeterminate"></div>
                </div>
                <p class="text-gray-400 mt-1">执行中，请稍候…</p>
              </div>
            </div>

            <div class="dashboard-bottom-grid">
              <div class="card glass compact-panel adaptive-bottom-card flex flex-col overflow-hidden">
                <div class="card-header">
                  <h3 class="card-title flex items-center gap-2">
                    <span>🤖</span> Agent 详情
                  </h3>
                </div>
                <div class="agent-mini-grid mb-3 shrink-0">
                  <div class="agent-mini-pill">
                    <span class="mini-label">Agent 总数</span>
                    <span class="mini-value">{{ totalAgents }}</span>
                  </div>
                  <div class="agent-mini-pill">
                    <span class="mini-label">运行中 Agent</span>
                    <span class="mini-value">{{ dashboardStore.status.agents?.subagents_running || 0 }}</span>
                  </div>
                  <div class="agent-mini-pill">
                    <span class="mini-label">执行中任务</span>
                    <span class="mini-value">{{ runningTasks }}</span>
                  </div>
                  <div class="agent-mini-pill">
                    <span class="mini-label">主模型</span>
                    <span class="mini-value truncate">{{ activeModelLabel }}</span>
                  </div>
                </div>
                <div class="agent-summary-row mb-2">
                  <span class="chip !text-xs">{{ dashboardStore.status.system?.gateway?.running ? '网关在线' : '网关离线' }}</span>
                  <span class="chip !text-xs">刷新: {{ dashboardRefreshLabel }}</span>
                  <span class="chip !text-xs">记录: {{ agentRunsPreview.length }}</span>
                </div>
                <div :class="agentRunsScrollable ? 'panel-scroll-conditional hover-scroll pr-1 flex-1 min-h-0' : 'pr-1 flex-1 min-h-0'">
                  <div v-if="agentRunsPreview.length === 0" class="empty-hint h-full justify-center">
                    <p>暂无子 Agent 运行记录</p>
                    <p class="text-gray-500">最近刷新：{{ dashboardStore.lastUpdated?.toLocaleTimeString() || '刚刚' }} / 等待新任务</p>
                  </div>
                  <div v-else class="space-y-2">
                    <div v-for="run in agentRunsPreview" :key="run.run_id" class="agent-run-item">
                      <div class="min-w-0">
                        <p class="truncate">{{ run.agent_name || 'Unnamed Agent' }}</p>
                        <p class="text-gray-500 truncate">{{ run.run_id }}</p>
                      </div>
                      <span class="chip" :class="agentRunTone(run.status)">
                        {{ run.status }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="card glass compact-panel adaptive-bottom-card flex flex-col overflow-hidden">
                <div class="card-header">
                  <h3 class="card-title flex items-center gap-2">
                    <span>🪙</span> 模型用量看板
                  </h3>
                  <button class="link-pill" @click="openModelSettings">模型设置</button>
                </div>
                <div :class="['model-usage-body', { 'is-scrollable hover-scroll': modelUsageScrollable }]">
                  <div class="space-y-2">
                    <div v-if="modelUsagePanels.length > 0" class="flex flex-wrap gap-2">
                      <button
                        v-for="panel in modelUsagePanels"
                        :key="panel.key"
                        class="tab"
                        :class="{ active: usagePanelTabSafe === panel.key }"
                        @click="usagePanelTab = panel.key"
                      >
                        {{ panel.title }}
                      </button>
                    </div>
                    <div v-if="activeUsagePanel" class="space-y-2">
                      <div class="flex justify-between items-center">
                        <span class="text-gray-400">数据源</span>
                        <span class="chip !text-xs">{{ activeUsagePanel.source }}</span>
                      </div>
                      <template v-if="activeUsagePanel.type === 'empty'">
                        <div class="empty-hint">
                          <p>{{ activeUsagePanel.message || '该模型已开启，但尚未完成 API 配置。' }}</p>
                          <p v-if="activeUsagePanel.missingFields?.length" class="text-gray-500">
                            缺少字段：{{ activeUsagePanel.missingFields.join(', ') }}
                          </p>
                        </div>
                      </template>
                      <template v-else-if="activeUsagePanel.type === 'quota'">
                        <div class="flex justify-between items-center">
                          <span class="text-gray-400">已用 / 配额</span>
                          <span class="font-bold text-openclaw-300">{{ activeUsagePanel.usedDisplay }}</span>
                        </div>
                        <div v-if="activeUsagePanel.percent !== null" class="flex justify-between items-center">
                          <span class="text-gray-400">已用占比</span>
                          <span class="font-mono">{{ formatPercent(Number(activeUsagePanel.percent)) }}</span>
                        </div>
                        <div v-if="activeUsagePanel.percent !== null" class="progress-bar">
                          <div class="progress-bar-inner static" :style="{ width: activeUsagePanel.percent + '%' }"></div>
                        </div>
                        <div v-if="activeUsagePanel.refreshWindow" class="flex justify-between items-center">
                          <span class="text-gray-400">剩余刷新时长</span>
                          <span class="font-mono">{{ activeUsagePanel.refreshWindow }}</span>
                        </div>
                        <div v-if="activeUsagePanel.remainingText !== null && activeUsagePanel.remainingText !== undefined" class="flex justify-between items-center">
                          <span class="text-gray-400">剩余额度</span>
                          <span class="font-mono">{{ activeUsagePanel.remainingText }}</span>
                        </div>
                        <div v-if="activeUsagePanel.modelNames?.length" class="flex flex-wrap gap-2">
                          <span v-for="name in activeUsagePanel.modelNames" :key="name" class="chip !text-xs">
                            {{ name }}
                          </span>
                        </div>
                        <p v-if="activeUsagePanel.notes" class="text-gray-400">{{ activeUsagePanel.notes }}</p>
                      </template>
                      <template v-else>
                        <div class="flex justify-between items-center">
                          <span class="text-gray-400">模型</span>
                          <span class="font-mono truncate max-w-[60%] text-right">{{ activeUsagePanel.model || activeUsagePanel.title }}</span>
                        </div>
                        <div class="flex justify-between items-center">
                          <span class="text-gray-400">运行中任务</span>
                          <span class="font-mono">{{ activeUsagePanel.runningTasks ?? 0 }}</span>
                        </div>
                        <div class="flex justify-between items-center">
                          <span class="text-gray-400">运行中 Agent</span>
                          <span class="font-mono">{{ activeUsagePanel.runningAgents ?? 0 }}</span>
                        </div>
                        <div class="flex justify-between items-center">
                          <span class="text-gray-400">计数源</span>
                          <span class="text-gray-300">{{ activeUsagePanel.metricStatus || '待接入' }}</span>
                        </div>
                        <p v-if="activeUsagePanel.message" class="text-gray-300">{{ activeUsagePanel.message }}</p>
                        <p v-if="activeUsagePanel.notes" class="text-gray-400">{{ activeUsagePanel.notes }}</p>
                      </template>
                      <div class="flex justify-between items-center">
                        <span class="text-gray-400">最近刷新</span>
                        <span class="font-mono">{{ dashboardRefreshLabel }}</span>
                      </div>
                    </div>
                    <div v-else class="empty-hint">
                      <p>暂未配置模型用量源</p>
                      <p class="text-gray-500">点击右上角「模型设置」接入 MiniMax / OpenAI / Gemini / GLM。</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="card glass task-main-card flex flex-col">
            <div class="card-header items-center">
              <div class="flex items-center gap-2">
                <span>📋</span>
                <h3 class="card-title">任务</h3>
                <span v-if="dashboardStore.status.todos?.length" class="px-2 py-0.5 bg-yellow-600 rounded text-xs">
                  {{ dashboardStore.status.todos.length }}
                </span>
              </div>
              <div class="flex items-center gap-3">
                <button class="link-pill" @click="openHistory = true; loadHistory()">历史任务</button>
              </div>
            </div>

            <button class="btn btn-primary !py-2 mb-3" @click="openCreateTodo = true">
              + 新建任务
            </button>

            <div class="task-list hover-scroll flex-1 min-h-0 overflow-y-auto pr-1">
              <div v-if="!dashboardStore.status.todos?.length" class="text-gray-500 text-center py-10 px-3">
                <p class="mb-2">📭 当前没有待办任务</p>
                <p class="text-gray-500">可先新建任务。</p>
              </div>
              <div
                v-for="todo in dashboardStore.status.todos"
                :key="todo.id"
                class="task-item"
              >
                <span class="mt-0.5">○</span>
                <div class="flex-1 min-w-0">
                  <p class="break-words">{{ todo.title }}</p>
                  <p v-if="todo.due_date" class="text-gray-500 mt-1">📅 {{ todo.due_date }}</p>
                </div>
                <button class="chip !text-xs" @click="completeTodoItem(todo.id)">完成</button>
              </div>
            </div>
          </div>
        </section>

        <p class="text-center text-gray-500 shrink-0">
          🕐 最后更新: {{ dashboardStore.lastUpdated?.toLocaleTimeString() || '从未' }}
        </p>
      </div>
    </main>
  </div>

  <div v-if="openHistory" class="fixed inset-0 bg-black/60 z-30 flex items-center justify-center p-3" @click.self="openHistory = false">
    <div class="card glass w-full max-w-2xl p-4 max-h-[min(85dvh,900px)] overflow-y-auto">
      <div class="card-header">
        <h3 class="card-title">历史任务</h3>
        <button class="text-gray-300 hover:text-white" @click="openHistory = false">关闭</button>
      </div>
      <div class="space-y-2 max-h-80 overflow-y-auto">
        <div v-if="dashboardStore.historyLoading" class="text-gray-400 text-center py-4">⏳ 拉取历史记录…</div>
        <div v-else-if="historySlice.length === 0" class="text-gray-500 text-center py-4">
          📭 暂无历史记录
        </div>
        <div v-else v-for="task in historySlice" :key="task.id || task.title" class="task-item">
          <span class="mt-0.5">◆</span>
          <div class="flex-1 min-w-0">
            <p class="break-words">{{ task.title }}</p>
            <p v-if="task.completed_at" class="text-gray-500">{{ task.completed_at }}</p>
          </div>
          <button v-if="task.source !== 'apple_reminders'" class="chip !text-xs" @click="reopenHistoryItem(task.id)">恢复</button>
        </div>
      </div>
    </div>
  </div>

  <div v-if="openCreateTodo" class="fixed inset-0 bg-black/60 z-30 flex items-center justify-center p-3" @click.self="closeCreateModal">
    <div class="card glass w-full max-w-lg p-4 max-h-[min(85dvh,900px)] overflow-y-auto">
      <div class="card-header">
        <h3 class="card-title">新建任务</h3>
        <button class="text-gray-300 hover:text-white" @click="closeCreateModal">关闭</button>
      </div>
      <div class="space-y-3">
        <input v-model="newTodoTitle" type="text" class="input !py-2" placeholder="任务标题（必填）" />
        <label class="inline-flex items-center gap-2 text-gray-300">
          <input v-model="includeTodoDue" type="checkbox" />
          设置时间（可选）
        </label>
        <input v-if="includeTodoDue" v-model="newTodoDue" type="datetime-local" class="input !py-2" />
        <p v-if="todoCreateMessage" class="text-gray-300">{{ todoCreateMessage }}</p>
      </div>
      <div class="mt-4 flex justify-end gap-2">
        <button class="btn btn-secondary !py-2" @click="closeCreateModal">取消</button>
        <button class="btn btn-primary !py-2" :disabled="creatingTodo" @click="submitTodo">
          {{ creatingTodo ? '创建中...' : '创建任务' }}
        </button>
      </div>
    </div>
  </div>

  <div v-if="openModelConfig" class="fixed inset-0 bg-black/60 z-30 flex items-center justify-center p-3" @click.self="openModelConfig = false">
    <div class="card glass w-full max-w-3xl p-4 max-h-[min(85dvh,900px)] overflow-y-auto">
      <div class="card-header">
        <h3 class="card-title">模型配置</h3>
        <button class="text-gray-300 hover:text-white" @click="openModelConfig = false">关闭</button>
      </div>

      <div class="space-y-3">
        <div v-for="provider in providerOrder" :key="provider.key" class="model-config-card">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="font-semibold">{{ provider.title }}</p>
              <p class="text-gray-400">{{ provider.hint }}</p>
            </div>
            <label class="inline-flex items-center gap-2 text-gray-300">
              <input v-model="modelConfigForm[provider.key].enabled" type="checkbox" />
              启用
            </label>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
            <template v-for="field in provider.fields" :key="field.key">
              <div
                v-if="field.secret && field.key === 'api_key' && providerHasApiKey(provider.key) && !apiKeyEditing[provider.key]"
                class="flex items-center gap-2"
              >
                <input
                  type="text"
                  class="input !py-2 flex-1"
                  :value="providerMaskedKey(provider.key)"
                  readonly
                />
                <button class="chip !text-xs shrink-0" @click="startEditApiKey(provider.key)">修改</button>
              </div>
              <input
                v-else
                v-model="modelConfigForm[provider.key][field.key]"
                :type="field.secret ? 'password' : 'text'"
                class="input !py-2"
                :placeholder="fieldPlaceholder(provider.key, field)"
              />
            </template>
          </div>
          <div class="mt-2 flex items-center gap-2">
            <button class="btn btn-secondary !py-2" :disabled="dashboardStore.integrationLoading" @click="validateProvider(provider.key)">
              {{ validatingProvider === provider.key ? '验证中...' : `验证 ${provider.title}` }}
            </button>
            <span v-if="providerValidateMessages[provider.key]" class="text-gray-300">{{ providerValidateMessages[provider.key] }}</span>
          </div>
        </div>

        <p v-if="modelConfigMessage" class="text-gray-300">{{ modelConfigMessage }}</p>
      </div>

      <div class="mt-4 flex justify-end gap-2">
        <button class="btn btn-secondary !py-2" @click="openModelConfig = false">取消</button>
        <button class="btn btn-primary !py-2" :disabled="dashboardStore.integrationLoading" @click="saveModelConfig">
          {{ dashboardStore.integrationLoading ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useDashboardStore } from '../stores/dashboard'
import JarvisAvatar from '../components/JarvisAvatar.vue'

const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()

const actionLoading = ref(false)
const openHistory = ref(false)
const showAlerts = ref(false)
const alertsWrap = ref(null)
const openCreateTodo = ref(false)
const includeTodoDue = ref(false)
const newTodoTitle = ref('')
const newTodoDue = ref('')
const creatingTodo = ref(false)
const todoCreateMessage = ref('')
const openModelConfig = ref(false)
const modelConfigMessage = ref('')
const validatingProvider = ref('')
const providerValidateMessages = ref({})
const apiKeyEditing = ref({})

const gatewayStatusColor = computed(() => (
  dashboardStore.status?.system?.gateway?.running ? 'text-green-400' : 'text-red-400'
))

const jarvisState = computed(() => {
  if (dashboardStore.error) return 'alert'
  if (!dashboardStore.status) return 'booting'
  const cpu = dashboardStore.status.system?.cpu_percent || 0
  const mem = dashboardStore.status.system?.memory_percent || 0
  if (!dashboardStore.status.system?.gateway?.running) return 'offline'
  if (cpu > 85 || mem > 85) return 'warning'
  return 'ready'
})

const jarvisMoodLabel = computed(() => ({
  booting: '加载中',
  thinking: '分析中',
  ready: '全功率待命',
  warning: '资源预警',
  alert: '异常告警',
  offline: '离线'
}[jarvisState.value] || '待命'))

const jarvisMessage = computed(() => ({
  booting: '正在唤醒系统，准备接管控制面板。',
  thinking: '正在解析数据流和健康指标…',
  ready: '所有子系统正常，随时可执行指令。',
  warning: '资源接近阈值，建议关注运行负载。',
  alert: `检测到异常：${dashboardStore.error || '请检查日志'}`,
  offline: 'Gateway 已停止，部分操作不可用。'
}[jarvisState.value] || '保持链接畅通。'))

const jarvisMoodClass = computed(() => ({
  booting: 'text-openclaw-200',
  thinking: 'text-openclaw-200',
  ready: 'text-green-300',
  warning: 'text-amber-300',
  alert: 'text-red-300',
  offline: 'text-gray-300'
}[jarvisState.value] || 'text-openclaw-200'))

const jarvisFace = computed(() => ({
  booting: '🛰️',
  thinking: '🧠',
  ready: '🛡️',
  warning: '⚠️',
  alert: '🚨',
  offline: '🪫'
}[jarvisState.value] || '🤖'))

const totalAgents = computed(() => {
  const subs = dashboardStore.status?.agents?.subagents_running || 0
  return 1 + subs
})

const activeModelLabel = computed(() => dashboardStore.status?.agents?.main_agent?.model || 'Unknown')

const runningTasks = computed(() => (
  dashboardStore.status?.agents?.running_tasks_count ??
  (dashboardStore.status?.agents?.running_tasks?.length ?? 0)
))
const dashboardRefreshLabel = computed(() => dashboardStore.lastUpdated?.toLocaleTimeString() || '刚刚')

const providerOrder = [
  {
    key: 'minimax',
    title: 'MiniMax',
    hint: '支持真实计数（Coding Plan）',
    fields: [
      { key: 'api_key', label: 'API Key', required: true, secret: true },
      { key: 'group_id', label: 'Group ID', required: false },
      { key: 'quota_url', label: 'Quota URL', required: false }
    ]
  },
  {
    key: 'openai',
    title: 'OpenAI (GPT)',
    hint: '支持官方 Usage API 请求量统计',
    fields: [
      { key: 'api_key', label: 'Admin API Key', required: true, secret: true },
      { key: 'project_id', label: 'Project ID', required: false },
      { key: 'organization_id', label: 'Organization ID', required: false }
    ]
  },
  {
    key: 'gemini',
    title: 'Gemini',
    hint: '当前展示状态摘要，计数源后续接入',
    fields: [
      { key: 'api_key', label: 'API Key', required: true, secret: true },
      { key: 'project_id', label: 'Project ID', required: false }
    ]
  },
  {
    key: 'glm',
    title: 'GLM',
    hint: '当前展示状态摘要，计数源后续接入',
    fields: [
      { key: 'api_key', label: 'API Key', required: true, secret: true },
      { key: 'base_url', label: 'Base URL', required: false }
    ]
  }
]

const modelConfigForm = ref(providerOrder.reduce((acc, item) => {
  acc[item.key] = { enabled: false }
  item.fields.forEach((f) => {
    acc[item.key][f.key] = ''
  })
  return acc
}, {}))

const modelUsagePanels = computed(() => {
  const rawPanels = dashboardStore.status?.usage_panels
  if (Array.isArray(rawPanels) && rawPanels.length > 0) {
    return rawPanels.map((item) => {
      const used = item?.used ?? null
      const total = item?.total ?? null
      return {
        key: item?.key || 'panel-unknown',
        type: item?.type || 'status',
        title: item?.title || 'Model',
        panelState: item?.panel_state || null,
        source: item?.source || '未知',
        usedDisplay: `${used ?? '--'} / ${total ?? '--'}`,
        remainingText: item?.remaining_text ?? null,
        refreshWindow: item?.refresh_window ?? null,
        percent: item?.percent ?? null,
        modelNames: Array.isArray(item?.models) ? item.models : [],
        model: item?.model || item?.title || '',
        runningTasks: item?.running_tasks ?? runningTasks.value,
        runningAgents: item?.running_agents ?? (dashboardStore.status?.agents?.subagents_running || 0),
        metricStatus: item?.metric_status || (item?.type === 'quota' ? '已接入' : '待接入'),
        message: item?.message || null,
        missingFields: Array.isArray(item?.missing_fields) ? item.missing_fields : [],
        notes: item?.notes || null
      }
    })
  }

  // Fallback for older backend payloads.
  const minimax = dashboardStore.status?.minimax || dashboardStore.status?.system?.minimax
  if (!minimax) return []
  const total = Number(minimax?.total || 0)
  const used = Number(minimax?.used || 0)
  const percent = total > 0 ? Number(((used / total) * 100).toFixed(1)) : null
  return [{
    key: 'minimax',
    type: 'quota',
    title: 'MiniMax',
    panelState: 'ready',
    source: '兼容模式',
    usedDisplay: `${used || '--'} / ${total || '--'}`,
    remainingText: minimax?.remaining ?? null,
    refreshWindow: null,
    percent,
    modelNames: Array.isArray(minimax?.models) ? minimax.models.map((x) => x.model_name).filter(Boolean) : [],
    model: 'MiniMax',
    runningTasks: runningTasks.value,
    runningAgents: dashboardStore.status?.agents?.subagents_running || 0,
    metricStatus: '兼容模式',
    message: null,
    missingFields: [],
    notes: '建议升级后端以启用多模型面板'
  }]
})
const usagePanelTab = ref('minimax')
const usagePanelTabSafe = computed(() => {
  if (!modelUsagePanels.value.length) return null
  return modelUsagePanels.value.some((item) => item.key === usagePanelTab.value)
    ? usagePanelTab.value
    : modelUsagePanels.value[0].key
})
const activeUsagePanel = computed(() => {
  if (!usagePanelTabSafe.value) return null
  return modelUsagePanels.value.find((item) => item.key === usagePanelTabSafe.value) || null
})
const modelUsageScrollable = computed(() => {
  if (!activeUsagePanel.value) return false
  const modelNameCount = Array.isArray(activeUsagePanel.value.modelNames) ? activeUsagePanel.value.modelNames.length : 0
  return modelUsagePanels.value.length > 3 || modelNameCount > 3
})

const healthScore = computed(() => {
  const cpu = dashboardStore.status?.system?.cpu_percent || 0
  const mem = dashboardStore.status?.system?.memory_percent || 0
  const gatewayOk = dashboardStore.status?.system?.gateway?.running ? 0 : 30
  return Math.max(0, Math.round(100 - (cpu + mem) / 4 - gatewayOk))
})

const heroGroups = computed(() => {
  const system = dashboardStore.status?.system || {}
  const channels = dashboardStore.status?.channels || {}
  const cpu = Number(system.cpu_percent || 0)
  const mem = Number(system.memory_percent || 0)

  const toneByPercent = (value) => {
    if (value >= 85) return 'error'
    if (value >= 65) return 'warn'
    return 'normal'
  }
  const toneByBool = (enabled) => (enabled ? 'normal' : 'error')

  return [
    {
      key: 'system',
      title: '系统',
      icon: '🖥️',
      items: [
        { key: 'gw', icon: '🧭', label: 'Gateway', value: system.gateway?.running ? '运行中' : '停止', tone: toneByBool(system.gateway?.running) },
        { key: 'health', icon: '💚', label: '健康度', value: `${healthScore.value}%`, tone: healthScore.value < 50 ? 'error' : healthScore.value < 75 ? 'warn' : 'normal' },
        { key: 'cpu', icon: '🧮', label: 'CPU', value: `${cpu.toFixed(1)}%`, tone: toneByPercent(cpu) },
        { key: 'mem', icon: '🧱', label: 'Memory', value: `${mem.toFixed(1)}%`, tone: toneByPercent(mem) }
      ]
    },
    {
      key: 'channels',
      title: '通道',
      icon: '📡',
      items: [
        { key: 'tg', icon: '✈️', label: 'Telegram', value: channels.telegram?.enabled ? 'ON' : 'OFF', tone: toneByBool(channels.telegram?.enabled) },
        { key: 'im', icon: '💬', label: 'iMessage', value: channels.imessage?.enabled ? 'ON' : 'OFF', tone: toneByBool(channels.imessage?.enabled) }
      ]
    }
  ]
})

const agentRunsPreview = computed(() => {
  const runs = dashboardStore.status?.agents?.subagent_runs || []
  return [...runs]
    .sort((a, b) => {
      const aRunning = a.status === 'running' ? 0 : 1
      const bRunning = b.status === 'running' ? 0 : 1
      if (aRunning !== bRunning) return aRunning - bRunning
      return String(b.start_time || '').localeCompare(String(a.start_time || ''))
    })
    .slice(0, 8)
})
const agentRunsScrollable = computed(() => agentRunsPreview.value.length > 6)

const historySlice = computed(() => (dashboardStore.historyTasks || []).slice(0, 30))

const alertItems = computed(() => {
  const items = []
  if (dashboardStore.error) {
    items.push({
      key: 'dashboard-error',
      title: '接口错误',
      detail: dashboardStore.error,
      count: 1
    })
  }
  const logs = dashboardStore.status?.logs || []
  logs.filter((log) => log.error_count > 0).forEach((log) => {
    items.push({
      key: `log-${log.file}`,
      title: log.file,
      detail: log.last_error || `异常 ${log.error_count}`,
      count: log.error_count
    })
  })
  return items
})

const alertCount = computed(() => alertItems.value.length)

function toggleAlerts() {
  showAlerts.value = !showAlerts.value
}

function closeAlerts() {
  showAlerts.value = false
}

function handleAlertsOutsideClick(event) {
  const root = alertsWrap.value
  if (!showAlerts.value || !root) return
  if (!root.contains(event.target)) {
    showAlerts.value = false
  }
}

onMounted(() => {
  document.addEventListener("pointerdown", handleAlertsOutsideClick)
})

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", handleAlertsOutsideClick)
})

function logout() {
  authStore.logout()
  router.push('/login')
}

async function refresh() {
  await dashboardStore.fetchDashboard(false)
}

function hydrateModelConfigForm() {
  const providers = dashboardStore.integrations?.providers || {}
  providerOrder.forEach((provider) => {
    const src = providers[provider.key] || {}
    modelConfigForm.value[provider.key].enabled = !!src.enabled
    apiKeyEditing.value[provider.key] = false
    provider.fields.forEach((field) => {
      modelConfigForm.value[provider.key][field.key] = src[field.key] || ''
    })
  })
}

async function openModelSettings() {
  modelConfigMessage.value = ''
  providerValidateMessages.value = {}
  const result = await dashboardStore.fetchIntegrations()
  if (!result.success) {
    modelConfigMessage.value = result.message || '加载模型配置失败'
  } else {
    hydrateModelConfigForm()
  }
  openModelConfig.value = true
}

async function saveModelConfig() {
  modelConfigMessage.value = ''
  const providers = {}
  providerOrder.forEach((provider) => {
    providers[provider.key] = {
      enabled: !!modelConfigForm.value[provider.key].enabled
    }
    provider.fields.forEach((field) => {
      providers[provider.key][field.key] = (modelConfigForm.value[provider.key][field.key] || '').trim()
    })
  })
  const result = await dashboardStore.saveIntegrations(providers)
  modelConfigMessage.value = result.message
  if (result.success) {
    hydrateModelConfigForm()
  }
}

async function validateProvider(providerKey) {
  validatingProvider.value = providerKey
  modelConfigMessage.value = ''
  const draft = { ...modelConfigForm.value[providerKey] }
  if (apiKeyEditing.value[providerKey] && (!draft.api_key || !draft.api_key.trim())) {
    draft.__clear_api_key = true
  }
  if (!apiKeyEditing.value[providerKey] && providerHasApiKey(providerKey) && (!draft.api_key || !draft.api_key.trim())) {
    delete draft.api_key
  }
  const result = await dashboardStore.validateDraftIntegration(providerKey, draft)
  providerValidateMessages.value = {
    ...providerValidateMessages.value,
    [providerKey]: result.success ? `✅ ${result.message}` : `❌ ${result.message}`
  }
  validatingProvider.value = ''
}

function fieldPlaceholder(providerKey, field) {
  const base = field.label + (field.required ? '（必填）' : '（可选）')
  if (!field.secret || field.key !== 'api_key') return base
  if (providerHasApiKey(providerKey) && apiKeyEditing.value[providerKey]) return '输入新 API Key（保存后生效）'
  return base
}

function providerHasApiKey(providerKey) {
  return !!dashboardStore.integrations?.providers?.[providerKey]?.has_api_key
}

function providerMaskedKey(providerKey) {
  return dashboardStore.integrations?.providers?.[providerKey]?.api_key_masked || ''
}

function startEditApiKey(providerKey) {
  apiKeyEditing.value[providerKey] = true
  modelConfigForm.value[providerKey].api_key = ''
}

async function restartGateway() {
  actionLoading.value = true
  const success = await dashboardStore.restartGateway()
  actionLoading.value = false
  alert(success ? '✅ 重启命令已发送' : `❌ 重启失败: ${dashboardStore.error}`)
}

async function createBackup() {
  actionLoading.value = true
  const success = await dashboardStore.createBackup()
  actionLoading.value = false
  alert(success ? '✅ 备份创建成功' : `❌ 备份失败: ${dashboardStore.error}`)
}

async function clearLogs() {
  actionLoading.value = true
  const success = await dashboardStore.clearLogs()
  actionLoading.value = false
  alert(success ? '✅ 日志已清除' : `❌ 操作失败: ${dashboardStore.error}`)
}

async function submitTodo() {
  const title = newTodoTitle.value.trim()
  if (!title) {
    todoCreateMessage.value = '请输入任务标题。'
    return
  }
  creatingTodo.value = true
  const payload = {
    title,
    list_name: '贾维斯的待办',
    due_date: includeTodoDue.value && newTodoDue.value ? new Date(newTodoDue.value).toISOString() : null
  }
  const result = await dashboardStore.createTodo(payload)
  creatingTodo.value = false
  todoCreateMessage.value = result.message
  if (result.success) {
    newTodoTitle.value = ''
    newTodoDue.value = ''
    includeTodoDue.value = false
    openCreateTodo.value = false
    await dashboardStore.fetchDashboard(false)
  }
}

async function completeTodoItem(taskId) {
  const result = await dashboardStore.completeTodo(taskId)
  if (!result.success) {
    alert(`❌ ${result.message}`)
    return
  }
  await dashboardStore.fetchDashboard(false)
  if (openHistory.value) {
    await dashboardStore.reloadHistoryTasks()
  }
}

async function reopenHistoryItem(taskId) {
  const result = await dashboardStore.reopenTask(taskId)
  if (!result.success) {
    alert(`❌ ${result.message}`)
    return
  }
  await dashboardStore.reloadHistoryTasks()
}

function closeCreateModal() {
  openCreateTodo.value = false
  includeTodoDue.value = false
  newTodoTitle.value = ''
  newTodoDue.value = ''
  todoCreateMessage.value = ''
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--%'
  return `${Number(value).toFixed(1)}%`
}

function confirmRestart() {
  const ok = confirm('⚠️ 重启 Gateway 将导致短暂不可用，确认继续？')
  if (ok) restartGateway()
}

function loadHistory() {
  if (!dashboardStore.historyLoaded && !dashboardStore.historyLoading) {
    dashboardStore.fetchHistoryTasks()
  }
}

function agentRunTone(status) {
  if (status === 'running') return 'run-tone-running'
  if (status === 'failed' || status === 'error') return 'run-tone-error'
  return 'run-tone-default'
}
</script>
