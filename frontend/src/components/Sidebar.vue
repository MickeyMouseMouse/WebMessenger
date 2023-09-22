<template>
  <div id='sidebar'>
    <div v-show='isMobile' style='display: flex; justify-content: flex-end; width: 100%; margin-bottom: 0.5em'>
      <Button class='p-button-rounded p-button-outlined' icon='pi pi-times' @click='closeSidebar' />
    </div>
    <div id='item_container' :class="{'item_container_mobile': isMobile}">
      <div :class="['item', $route.name=='Messenger' ? 'current_state' : 'unselected_item']"
        title='Messenger' @click="goTo('messenger')">
        <div :class="getUnreadIndicator ? 'pi pi-envelope alarm' : 'pi pi-comments'"
          style='padding-right: 0.3em' />
        <div v-if='isMobile'>Messenger</div>
      </div>
      <div :class="['item', $route.name=='Files' ? 'current_state' : 'unselected_item']"
        title='Files' @click="goTo('files')">
        <div class='pi pi-file' style='padding-right:0.3em' />
        <div v-if='isMobile'>Files</div>
      </div>
      <div :class="['item', $route.name=='Calls' ? 'current_state' : 'unselected_item']"
        title='Calls' @click="goTo('calls')">
        <div class='pi pi-phone' style='padding-right:0.3em' />
        <div v-if='isMobile'>Calls</div>
      </div>
      <div :class="['item', $route.name=='Settings' ? 'current_state' : 'unselected_item']"
        title='Settings' @click="goTo('settings')">
        <div class='pi pi-cog' style='padding-right:0.3em' />
        <div v-if='isMobile'>Settings</div>
      </div>
      <Button class='p-button-text p-button-danger' icon='pi pi-sign-out'
        title='Sign out' :label="isMobile ? 'Sign out' : ''"
        style='margin-top: 1em; white-space: nowrap' @click='sign_out_popup_visible = true' />
    </div>
    <PopUp :visible='sign_out_popup_visible' @keydown.esc='sign_out_popup_visible = false'
      header='Sign out' :modal='true' :closable='false' :draggable='false'>
      Are you sure you want to sign out?
      <template #footer>
        <Button label='No' icon='pi pi-times' class='p-button-text'
          @click='sign_out_popup_visible = false' />
        <Button label='Yes' icon='pi pi-check' autofocus
          @click='signOut' />
      </template>
    </PopUp>
</div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import makeHTTPRequest from '@/makeHTTPRequest'
export default {
	name: 'v-sidebar',
  setup() {
    const store = useStore()
    const router = useRouter()

    const sign_out_popup_visible = ref(false)

    const closeSidebar = () => store.dispatch('setMobileSidebarVisible', false)

    const goTo = (path) => {
      router.push({ path: '/account/' + path })
      closeSidebar()
    }

    async function signOut() {
      sign_out_popup_visible.value = false
      closeSidebar()
      store.dispatch('resetData')
      await makeHTTPRequest('/sign_out', 'POST')
      router.replace({'path': '/'})
    }

    const isMobile = computed(() => store.getters.isMobile)

    const getUnreadIndicator = computed(() => store.getters.getUnreadIndicator)

    return {
      sign_out_popup_visible,
      closeSidebar, goTo, signOut,
      isMobile, getUnreadIndicator
    }
  }
}
</script>

<style scoped>
#sidebar {
  display: flex;
  flex-flow: column;
  height: 100%;
  background-color: #edeef0;
  align-items: center;
  padding: 0.5em;
  box-shadow: 0px 0px 4px grey;
  z-index: 6;
}

#item_container {
  display: flex;
  flex-flow: column;
}

.item_container_mobile {
  margin: 0em 1em
}

.item {
  display: flex;
  align-items: center;
  padding: 0.5em 0.5em 0.5em 0.7em;
  margin: 0.2em 0em;
  cursor: pointer;
  border: 1px solid #edeef0;
}

.unselected_item {
  color: black;
}

.unselected_item:hover {
  border-image: repeating-linear-gradient(to bottom right, #2196F3, #edeef0, #edeef0, #2196F3) 1;
}

.current_state {
  color: #2196F3;
}

.alarm {
  color: red;
}
</style>
