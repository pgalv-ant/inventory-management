import { ref, watchEffect } from 'vue'

const STORAGE_KEY = 'inventory-theme'

// Module-scoped singleton: all components share the same reactive state
const isDark = ref(localStorage.getItem(STORAGE_KEY) === 'dark')

// Apply the class to <html> whenever isDark changes, and persist
watchEffect(() => {
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')
})

export function useTheme() {
  const toggle = () => { isDark.value = !isDark.value }
  return { isDark, toggle }
}
