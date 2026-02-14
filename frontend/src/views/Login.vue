<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-gray-900">
    <div class="w-full max-w-md">
      <!-- Logo/Title -->
      <div class="text-center mb-8">
        <span class="text-5xl mb-4 block">🤖</span>
        <h1 class="text-3xl font-bold text-openclaw-400 mb-2">OpenClaw</h1>
        <p class="text-gray-400">Dashboard</p>
      </div>

      <!-- Login Form -->
      <div class="card">
        <h2 class="text-xl font-semibold mb-6 text-center flex items-center justify-center gap-2">
          🔐 登录
        </h2>

        <form @submit.prevent="handleLogin">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
              👤 用户名
            </label>
            <input
              v-model="username"
              type="text"
              class="input"
              placeholder="输入用户名"
              required
            />
          </div>

          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
              🔑 密码
            </label>
            <input
              v-model="password"
              type="password"
              class="input"
              placeholder="输入密码"
              required
            />
          </div>

          <!-- Error message -->
          <div v-if="authStore.error" class="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
            ⚠️ {{ authStore.error }}
          </div>

          <!-- Login button -->
          <button
            type="submit"
            class="w-full btn btn-primary py-3 flex items-center justify-center gap-2"
            :disabled="authStore.loading"
          >
            <span v-if="authStore.loading">⏳ 登录中...</span>
            <span v-else>🚀 登录</span>
          </button>
        </form>
      </div>

      <!-- Footer -->
      <p class="text-center text-gray-500 text-sm mt-6">
        OpenClaw Dashboard v1.0
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')

async function handleLogin() {
  const success = await authStore.login(username.value, password.value)

  if (success) {
    router.push('/')
  }
}
</script>
