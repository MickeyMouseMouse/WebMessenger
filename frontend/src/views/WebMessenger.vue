<template>
  <div v-if='getSocket' id='webmessenger'>
    <v-sidebar v-if='isMobile' :class="['mobile_sidebar',
      getMobileSidebarVisible ? 'mobile_sidebar_opened' : 'mobile_sidebar_closed']" />
    <v-sidebar v-else />
    <div v-show='getMobileSidebarVisible' id='mobile_sidebar_background'
      @click='setMobileSidebarVisible(false)' />
    <div id='workplace'>
      <MobileHeader v-if='isMobile' />
      <router-view />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import MobileHeader from '@/components/MobileHeader.vue'
import vSidebar from '@/components/Sidebar.vue'
export default {
	name: 'v-web-messenger',
  components: {
    MobileHeader,
		vSidebar
	},
  setup() {
    const store = useStore()

    // on create
    if (!store.getters.getSocket) store.dispatch('connectSocketIO')

    const setMobileSidebarVisible = () => store.dispatch('setMobileSidebarVisible')

    const isMobile = computed(() => store.getters.isMobile)

    const getSocket = computed(() => store.getters.getSocket)

    const getMobileSidebarVisible = computed(() => store.getters.getMobileSidebarVisible)

    return {
      setMobileSidebarVisible,
      isMobile, getSocket, getMobileSidebarVisible
    }
  }
}
</script>

<style scoped>
#webmessenger {
  display: flex;
  flex: 1;
}

#mobile_sidebar_background {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 5;
}

.mobile_sidebar {
  position: absolute;
  height: 100%;
  z-index: 10;
}

.mobile_sidebar_closed {
  left: -50%;
  transition-duration: 0.2s;
}

.mobile_sidebar_opened {
  left: 0%;
  transition-duration: 0.2s;
}

#workplace {
  display: flex;
  flex-flow: column;
  flex: 1;
}
</style>
