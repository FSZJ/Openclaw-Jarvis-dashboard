import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = '/api'
let authInterceptorInstalled = false

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.post(`${API_URL}/auth/login`, {
          username,
          password
        })

        this.token = response.data.access_token
        this.user = response.data.user

        localStorage.setItem('token', this.token)
        localStorage.setItem('user', JSON.stringify(this.user))

        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`

        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Login failed'
        return false
      } finally {
        this.loading = false
      }
    },

    async changePassword(oldPassword, newPassword) {
      try {
        await axios.post(`${API_URL}/auth/change-password`, {
          old_password: oldPassword,
          new_password: newPassword
        })
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Password change failed'
        return false
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      delete axios.defaults.headers.common['Authorization']
    },

    initAxios() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
      }
    },

    setupAxiosInterceptors() {
      if (authInterceptorInstalled) return
      authInterceptorInstalled = true

      axios.interceptors.response.use(
        (response) => response,
        (error) => {
          const status = error?.response?.status
          const detail = String(error?.response?.data?.detail || '')
          const invalidToken = status === 401 && /invalid|expired token/i.test(detail)
          if (invalidToken) {
            this.logout()
            if (window.location.pathname !== '/login') {
              window.location.href = '/login'
            }
          }
          return Promise.reject(error)
        }
      )
    }
  }
})
