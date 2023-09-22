<template>
  <div id='mobile_header'>
    <div style='flex: 1'>
      <Button class='p-button-text' icon='pi pi-bars' @click='toggleSidebarVisible' />
    </div>
    <div style='display: flex; align-items: center; text-transform: capitalize;'>
      <strong>{{ $route.name }}</strong>
    </div>
    <div style='display: flex; flex: 1; justify-content: end; align-items: center'>
      <div v-show='getUnreadIndicator' id='new_message_indicator' class='pi pi-envelope' @click='openMessenger' />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
export default {
	name: 'v-mobile-header',
  setup() {
    const store = useStore()
    const router = useRouter()

    const toggleSidebarVisible = () => store.dispatch('setMobileSidebarVisible', !store.getters.getMobileSidebarVisible)

    const openMessenger = () => router.push({ path: '/account/messenger' })

    const getMobileSidebarVisible = computed(() => store.getters.getMobileSidebarVisible)

    const getUnreadIndicator = computed(() => store.getters.getUnreadIndicator)

    return {
      toggleSidebarVisible, openMessenger,
      getMobileSidebarVisible, getUnreadIndicator
    }
  }
}
</script>

<style scoped>
#mobile_header {
  display: flex;
  min-height: 2.5em;
  border-bottom: 1px solid lightgrey;
}

#new_message_indicator {
  color: red;
  margin-right: 0.5em;
}
</style>