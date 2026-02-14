<template>
  <div class="relative w-28 h-28 sm:w-32 sm:h-32 jarvis-avatar">
    <!-- outer glow ring -->
    <div class="absolute inset-0 rounded-full avatar-ring"></div>
    <!-- rotating gradient halo -->
    <div class="absolute inset-2 rounded-full avatar-halo"></div>
    <!-- core -->
    <svg viewBox="0 0 200 200" class="relative z-10 w-full h-full">
      <defs>
        <radialGradient id="core" cx="50%" cy="50%" r="60%">
          <stop offset="0%" :stop-color="colors.coreLight" stop-opacity="1" />
          <stop offset="60%" :stop-color="colors.coreMid" stop-opacity="0.9" />
          <stop offset="100%" :stop-color="colors.coreDark" stop-opacity="0.7" />
        </radialGradient>
        <linearGradient id="visor" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" :stop-color="colors.visor" stop-opacity="0.9" />
          <stop offset="100%" :stop-color="colors.visor" stop-opacity="0.2" />
        </linearGradient>
      </defs>
      <circle cx="100" cy="100" r="94" fill="url(#core)" :stroke="colors.ring" stroke-width="4" opacity="0.9" />
      <!-- scan arc -->
      <path
        d="M100 16 A84 84 0 0 1 184 100"
        :stroke="colors.scan"
        stroke-width="6"
        stroke-linecap="round"
        fill="none"
        class="scan-arc"
      />
      <!-- visor -->
      <rect x="46" y="86" rx="12" ry="12" width="108" height="38" fill="url(#visor)" opacity="0.9" />
      <!-- eye pair -->
      <g :fill="colors.eye">
        <circle cx="78" cy="105" r="6" />
        <circle cx="122" cy="105" r="6" />
      </g>
      <!-- mouth status line -->
      <rect x="86" y="128" rx="2" width="28" height="4" :fill="colors.eye" />
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  mood: { type: String, default: 'ready' }
})

const palette = {
  ready:  { ring: '#38bdf8', scan: '#22d3ee', eye: '#d9f99d', visor: '#a5f3fc', coreLight: '#e0f2fe', coreMid: '#38bdf8', coreDark: '#0ea5e9' },
  thinking: { ring: '#8b5cf6', scan: '#a855f7', eye: '#c084fc', visor: '#a5b4fc', coreLight: '#ede9fe', coreMid: '#8b5cf6', coreDark: '#5b21b6' },
  warning: { ring: '#f59e0b', scan: '#f97316', eye: '#ffedd5', visor: '#fed7aa', coreLight: '#fff7ed', coreMid: '#fb923c', coreDark: '#c2410c' },
  alert: { ring: '#ef4444', scan: '#f43f5e', eye: '#fecdd3', visor: '#fecdd3', coreLight: '#fee2e2', coreMid: '#fb7185', coreDark: '#b91c1c' },
  offline: { ring: '#6b7280', scan: '#9ca3af', eye: '#e5e7eb', visor: '#d1d5db', coreLight: '#f3f4f6', coreMid: '#9ca3af', coreDark: '#4b5563' },
  booting: { ring: '#38bdf8', scan: '#67e8f9', eye: '#e0f2fe', visor: '#bae6fd', coreLight: '#e0f2fe', coreMid: '#67e8f9', coreDark: '#0284c7' }
}

const colors = computed(() => palette[props.mood] || palette.ready)
</script>

<style scoped>
.jarvis-avatar {
  filter: drop-shadow(0 20px 40px rgba(0, 0, 0, 0.35));
}
.avatar-ring {
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 30px rgba(56, 189, 248, 0.35);
}
.avatar-halo {
  background: conic-gradient(from 90deg, rgba(56,189,248,0.3), rgba(59,130,246,0.25), rgba(56,189,248,0.3));
  animation: spin 10s linear infinite;
  filter: blur(10px);
  opacity: 0.9;
}
.scan-arc {
  animation: arc 3.6s ease-in-out infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes arc {
  0% { stroke-dasharray: 0 600; stroke-dashoffset: 0; }
  50% { stroke-dasharray: 220 600; stroke-dashoffset: -80; }
  100% { stroke-dasharray: 0 600; stroke-dashoffset: -220; }
}
</style>
