<template>
  <div class="stat-card">
    <div class="flex items-center justify-between">
      <div>
        <p class="stat-label">{{ title }}</p>
        <p class="stat-value" :class="valueClass">{{ value }}</p>
      </div>
      <div class="w-3 h-3 rounded-full" :class="statusClass"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  value: [String, Number],
  status: {
    type: String,
    default: 'success'  // success, warning, error
  }
})

const statusClass = computed(() => {
  switch (props.status) {
    case 'success': return 'bg-green-500'
    case 'warning': return 'bg-yellow-500'
    case 'error': return 'bg-red-500'
    default: return 'bg-gray-500'
  }
})

const valueClass = computed(() => {
  switch (props.status) {
    case 'success': return 'text-green-400'
    case 'warning': return 'text-yellow-400'
    case 'error': return 'text-red-400'
    default: return 'text-white'
  }
})
</script>
