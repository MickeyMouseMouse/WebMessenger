<template>
  <router-view />
  <Toast :position="isDesktop ? 'top-right' : 'top-center'" style='opacity: 1' />
</template>

<script>
import { computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
export default {
  name: 'app',
  setup() {
    const store = useStore()
    const toast = useToast()

    const isDesktop = computed(() => store.getters.isDesktop)

    watch(() => store.getters.getSocketError, (error) => {
      if (error) toast.add({severity: 'error', summary: error.summary, detail: error.detail, life: 5000})
    })
    
    return {
      isDesktop
    }
  }
}
</script>

<style>
.p-toast-detail {
  white-space: pre-wrap;
}
</style>
