<template>
  <div class="min-h-screen bg-gray-900">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from './stores/dashboard'

const dashboardStore = useDashboardStore()

onMounted(() => {
  dashboardStore.startAutoRefresh()
})

onUnmounted(() => {
  dashboardStore.stopAutoRefresh()
})
</script>
