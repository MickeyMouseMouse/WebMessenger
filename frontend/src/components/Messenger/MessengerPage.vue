<template>
  <div id="messenger-page">
    <div :class="{'selector-desktop': isDesktop, 'mobile-panel': isMobile,
      'hidden-panel': isMobile && isChatOpen}">
      <Selector />
    </div>
    <div :class="{'chat-desktop': isDesktop, 'mobile-panel': isMobile,
      'hidden-panel': isMobile && !isChatOpen}">
      <Chat />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import Selector from "./PageContent/Selector.vue"
import Chat from "./PageContent/Chat/Chat.vue"
export default {
  name: "v-messenger-page",
  components: {
    Selector,
    Chat
  },
  setup() {
    const store = useStore()

    const isDesktop = computed(() => store.getters.isDesktop)

    const isMobile = computed(() => store.getters.isMobile)

    const isChatOpen = computed(() => store.getters.isChatOpen)

    return {
      isDesktop, isMobile, isChatOpen
    }
  }
}
</script>

<style scoped>
#messenger-page {
  display: flex;
  flex: 1;
  overflow: auto;
}

.selector-desktop {
  width: 18em;
  border-right: 1px solid lightgray;
}

.chat-desktop {
  display: flex;
  flex: 1;
}

.mobile-panel {
  display: flex;
  flex: 1;
}

.hidden-panel {
  display: none;
}
</style>
