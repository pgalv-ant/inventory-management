<template>
  <button
    class="theme-toggle"
    @click="toggle"
    :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
  >
    <svg v-if="isDark" width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="9" cy="9" r="4"/>
      <path d="M9 1v2M9 15v2M1 9h2M15 9h2M3.5 3.5l1.4 1.4M13.1 13.1l1.4 1.4M3.5 14.5l1.4-1.4M13.1 4.9l1.4-1.4"/>
    </svg>
    <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <path d="M15 9.5A6 6 0 1 1 8.5 3 4.5 4.5 0 0 0 15 9.5z"/>
    </svg>
  </button>
</template>

<script>
import { useTheme } from '../composables/useTheme'

export default {
  name: 'DarkModeToggle',
  setup() {
    const { isDark, toggle } = useTheme()
    return { isDark, toggle }
  }
}
</script>

<style scoped>
.theme-toggle {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  color: var(--color-text-secondary);
  border-radius: 6px;
  display: flex;
  align-items: center;
}
.theme-toggle:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}
</style>
