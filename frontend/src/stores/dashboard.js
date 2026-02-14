import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = '/api'
const HEAVY_ARRAY_KEYS = ['todos', 'completed_tasks', 'logs', 'usage_panels']

function mergeStatusPayload(current, incoming, preserveHeavy = false) {
  if (!current) return incoming
  if (!incoming) return current

  const merged = { ...current, ...incoming }
  if (!preserveHeavy) return merged

  for (const key of HEAVY_ARRAY_KEYS) {
    const nextVal = incoming[key]
    const prevVal = current[key]
    if (Array.isArray(nextVal) && nextVal.length === 0 && Array.isArray(prevVal) && prevVal.length > 0) {
      merged[key] = prevVal
    }
  }

  if ((incoming.minimax === null || incoming.minimax === undefined) && current.minimax) {
    merged.minimax = current.minimax
  }

  return merged
}

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    status: null,
    loading: false,
    error: null,
    lastUpdated: null,
    autoRefresh: true,
    refreshInterval: null,
    ws: null,
    wsConnected: false,
    wsRetryTimer: null,
    wsReconnectAttempts: 0,
    refreshTick: 0,
    historyTasks: [],
    historyLoading: false,
    historyLoaded: false,
    integrations: null,
    integrationLoading: false
  }),

  actions: {
    async fetchDashboard(light = false) {
      const firstLoad = !this.status
      if (firstLoad) this.loading = true
      try {
        const response = await axios.get(`${API_URL}/dashboard`, { params: light ? { light: 1 } : {} })
        this.status = mergeStatusPayload(this.status, response.data, light)
        this.lastUpdated = new Date()
        this.error = null
      } catch (err) {
        // Backward-compatible fallback for older backend without /api/dashboard
        await this.fetchStatus(light)
      } finally {
        if (firstLoad) this.loading = false
      }
    },

    async fetchStatus(light = false) {
      const firstLoad = !this.status
      if (firstLoad) this.loading = true
      try {
        const response = await axios.get(`${API_URL}/status/`, { params: light ? { light: 1 } : {} })
        this.status = mergeStatusPayload(this.status, response.data, light)
        this.lastUpdated = new Date()
        this.error = null
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch status'
      } finally {
        if (firstLoad) this.loading = false
      }
    },

    async restartGateway() {
      try {
        await axios.post(`${API_URL}/actions/gateway/restart`)
        await this.fetchDashboard()
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to restart gateway'
        return false
      }
    },

    async createBackup() {
      try {
        await axios.post(`${API_URL}/actions/backup`)
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to create backup'
        return false
      }
    },

    async clearLogs() {
      try {
        await axios.post(`${API_URL}/actions/logs/clear`)
        await this.fetchDashboard()
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to clear logs'
        return false
      }
    },

    startAutoRefresh(intervalMs = 60000) {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
      }
      this.disconnectWebSocket()
      // Fetch light first for faster first paint, then full data from aggregated endpoint
      this.fetchDashboard(true)
      setTimeout(() => this.fetchDashboard(false), 800)
      this.connectWebSocket()
      this.refreshInterval = setInterval(() => {
        if (this.autoRefresh) {
          this.refreshTick += 1
          const loadFull = this.refreshTick % 5 === 0
          this.fetchDashboard(!loadFull)
        }
      }, intervalMs)
    },

    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
      this.disconnectWebSocket()
    },

    connectWebSocket() {
      if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
        return
      }

      const token = localStorage.getItem('token')
      if (!token) return

      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const wsUrl = `${protocol}://${window.location.host}/ws?token=${encodeURIComponent(token)}`
      const socket = new WebSocket(wsUrl)
      this.ws = socket

      socket.onopen = () => {
        this.wsConnected = true
        this.wsReconnectAttempts = 0
        this.error = null
      }

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'status_update' && message.payload) {
            this.status = mergeStatusPayload(this.status, message.payload, true)
            this.lastUpdated = new Date()
          }
        } catch (_) {
          // ignore malformed ws payload
        }
      }

      socket.onerror = () => {
        this.wsConnected = false
      }

      socket.onclose = () => {
        this.wsConnected = false
        this.ws = null
        if (!this.autoRefresh) return
        if (this.wsReconnectAttempts >= 3) return

        if (this.wsRetryTimer) {
          clearTimeout(this.wsRetryTimer)
        }
        const delay = Math.min(15000, 2000 * (this.wsReconnectAttempts + 1))
        this.wsReconnectAttempts += 1
        this.wsRetryTimer = setTimeout(() => this.connectWebSocket(), delay)
      }
    },

    disconnectWebSocket() {
      if (this.wsRetryTimer) {
        clearTimeout(this.wsRetryTimer)
        this.wsRetryTimer = null
      }
      if (this.ws) {
        this.ws.close()
        this.ws = null
      }
      this.wsConnected = false
      this.wsReconnectAttempts = 0
    },

    async fetchHistoryTasks() {
      if (this.historyLoading || this.historyLoaded) return
      this.historyLoading = true
      this.error = null
      try {
        const response = await axios.get(`${API_URL}/tasks/history`)
        this.historyTasks = response.data || []
        this.historyLoaded = true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to load history tasks'
      } finally {
        this.historyLoading = false
      }
    },

    async reloadHistoryTasks() {
      this.historyLoaded = false
      await this.fetchHistoryTasks()
    },

    async createTodo(payload) {
      try {
        const response = await axios.post(`${API_URL}/tasks/todos`, payload)
        if (response.data?.todos) {
          this.status = this.status || {}
          this.status.todos = response.data.todos
        } else {
          await this.fetchDashboard(false)
        }
        this.lastUpdated = new Date()
        this.error = null
        return { success: true, message: response.data?.message || '任务已创建' }
      } catch (err) {
        const message = err.response?.data?.detail || '创建任务失败'
        this.error = message
        return { success: false, message }
      }
    },

    async fetchIntegrations() {
      this.integrationLoading = true
      try {
        const response = await axios.get(`${API_URL}/integrations/models`)
        this.integrations = response.data
        this.error = null
        return { success: true, data: response.data }
      } catch (err) {
        const message = err.response?.data?.detail || '加载模型配置失败'
        this.error = message
        return { success: false, message }
      } finally {
        this.integrationLoading = false
      }
    },

    async saveIntegrations(providers) {
      this.integrationLoading = true
      try {
        const response = await axios.put(`${API_URL}/integrations/models`, { providers })
        this.integrations = response.data?.data || this.integrations
        await this.fetchDashboard(false)
        this.error = null
        return { success: true, message: response.data?.message || '保存成功' }
      } catch (err) {
        const message = err.response?.data?.detail || '保存模型配置失败'
        this.error = message
        return { success: false, message }
      } finally {
        this.integrationLoading = false
      }
    },

    async validateIntegration(provider, draftConfig = null) {
      this.integrationLoading = true
      try {
        const body = draftConfig ? { config: draftConfig } : {}
        const response = await axios.post(`${API_URL}/integrations/models/${provider}/validate`, body)
        this.error = null
        return { success: true, message: response.data?.message || '验证成功', data: response.data?.panel }
      } catch (err) {
        const message = err.response?.data?.detail || '验证失败'
        this.error = message
        return { success: false, message }
      } finally {
        this.integrationLoading = false
      }
    },

    async validateDraftIntegration(provider, draftConfig) {
      return this.validateIntegration(provider, draftConfig)
    },

    async completeTodo(taskId) {
      try {
        const response = await axios.post(`${API_URL}/tasks/todos/${taskId}/complete`)
        this.status = this.status || {}
        this.status.todos = response.data?.todos || []
        this.historyTasks = response.data?.history || this.historyTasks
        this.historyLoaded = true
        this.lastUpdated = new Date()
        this.error = null
        return { success: true, message: response.data?.message || '任务已完成' }
      } catch (err) {
        const message = err.response?.data?.detail || '完成任务失败'
        this.error = message
        return { success: false, message }
      }
    },

    async reopenTask(taskId) {
      try {
        const response = await axios.post(`${API_URL}/tasks/history/${taskId}/reopen`)
        this.status = this.status || {}
        this.status.todos = response.data?.todos || this.status.todos || []
        this.historyTasks = response.data?.history || this.historyTasks
        this.historyLoaded = true
        this.lastUpdated = new Date()
        this.error = null
        return { success: true, message: response.data?.message || '任务已恢复' }
      } catch (err) {
        const message = err.response?.data?.detail || '恢复任务失败'
        this.error = message
        return { success: false, message }
      }
    }
  }
})
