<template>
  <div id='selector'>
    <div id='toolbar'>
      <span class='p-input-icon-left' style='display: flex; flex: 1'>
        <i class='pi pi-search' />
        <InputText id='search-field' v-model='search_query' placeholder='Search chats'
          @keydown.esc="search_query = ''"/>
      </span>
      <Button v-show='current_mode == panel_modes.search'
        icon='pi pi-delete-left' class='p-button-rounded p-button-outlined'
        @click="search_query = ''" />
      <Button v-show='current_mode == panel_modes.chat_list'
        icon='pi pi-plus' class='p-button-rounded p-button-outlined'
        @click='(e) => $refs.menu.toggle(e)' />
      <Menu ref='menu' :model='menu_items' :popup='true' />
    </div>
    <div v-show='current_mode == panel_modes.chat_list' style='overflow: auto'>
      <div v-show='getChatList.length == 0' class='empty-list-label'>
        You don't have chats yet
      </div>
      <ItemList :list='getChatList' :active_item_id='getSelectedChatId' @select='openChat'/>
    </div>
    <div v-show='current_mode == panel_modes.search' style='overflow: auto'>
      <div v-if='search_result.length' style='padding: 0em 0.5em'>
        Search result:
      </div>
      <div v-else class='empty-list-label'>
        Nothing found
      </div>
      <ItemList :list='search_result' @select='searchResultHandler'/>
    </div>
  </div>

  <PopUp v-model:visible='new_group_popup_visible'
    header='New Group' :modal='true' :draggable='false'>
    <InputText v-model='new_group_name' placeholder='Name' autofocus @keydown.enter='createGroup' />
    <template #footer>
      <Button label='Create' :disabled='new_group_name.length == 0' @click='createGroup' />
    </template>
  </PopUp>

  <PopUp v-model:visible='new_channel_popup_visible'
    header='New Channel' :modal='true' :draggable='false'>
    <div style='display: flex; flex-flow: column;'>
      <InputText v-model='new_channel_name' placeholder='Name' autofocus @keydown.enter='createChannel' />
      <div style='display: flex; align-items: center; margin-top: 1em'>
          <div style='flex: 1; margin-right: 1em;'>
            Private
          </div>
          <Checkbox v-model='is_new_channel_private' :binary='true' />
      </div>
    </div>
    <template #footer>
      <Button label='Create' :disabled='new_channel_name.length == 0' @click='createChannel' />
    </template>
  </PopUp>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
import ItemList from '@/components/ItemList.vue'
export default {
  name: 'v-selector',
  components: {
    ItemList
  },
  setup() {
    const store = useStore()
    const toast = useToast()

    // on create
    store.dispatch('fetchUserChats')

    const panel_modes = {chat_list: 0, search: 1}
    const current_mode = ref(0)
    const menu_items = [
      {
        label: 'New Group',
        icon: 'pi pi-users',
        command: () => {
          new_group_name.value = ''
          new_group_popup_visible.value = true
        }
      },
      {
        label: 'New Channel',
        icon: 'pi pi-megaphone',
        command: () => {
          new_channel_name.value = ''
          is_new_channel_private.value = false
          new_channel_popup_visible.value = true
        }
      }
    ]
    const new_group_popup_visible = ref(false)
    const new_group_name = ref('')
    const new_channel_popup_visible = ref(false)
    const new_channel_name = ref('')
    const is_new_channel_private = ref(false)
    const search_query = ref('')
    const search_result = ref([])

    function search() {
      if (search_query.value.length == 0) return
      store.getters.getSocket.emit('/messenger/search', {
        'query': search_query.value,
        'types': ['user', 'channel']
      }, (r) => {
        if (r.status == 200) {
          search_result.value = r.search_result
        }
      })
    }

    function openChat(chat) {
      store.dispatch('fetchChatMessages', chat.id)
    }

    function searchResultHandler(item) {
      if (item.type == 'user') {
        store.getters.getSocket.emit('/messenger/create_dialog', {
            'interlocutor_id': item.id
        }, (r) => {
          if (r.status == 200) {
            store.dispatch('fetchChatMessages', r.chat_id)
          } else if (r.status == 403) {
            toast.add({severity: 'error', detail: r.error, life: 5000})
          }
        })
      } else if (item.type == 'channel') {
        store.dispatch('fetchChatInfo', item.id)
        store.dispatch('fetchChatMessages', item.id)
      }
      search_query.value = '' // watch trigger
    }

    function createGroup() {
      store.getters.getSocket.emit('/messenger/create_group', {
        'name': new_group_name.value
      }, (r) => {
        if (r.status == 200) {
          store.dispatch('fetchChatMessages', r.chat_id)
          new_group_popup_visible.value = false
        }
      })
    }

    function createChannel() {
      store.getters.getSocket.emit('/messenger/create_channel', {
        'name': new_channel_name.value,
        'is_private': is_new_channel_private.value
      }, (r) => {
        if (r.status == 200) {
          store.dispatch('fetchChatMessages', r.chat_id)
          new_channel_popup_visible.value = false
        } else if (r.status == 409) {
          toast.add({severity: 'error',
            detail: 'Such channel already exists',
            life: 5000})
        }
      })
    }

    const getChatList = computed(() => store.getters.getChatList)

    const getSelectedChatId = computed(() => store.getters.getSelectedChatId)

    watch(search_query, () => {
      if (search_query.value.length > 0) {
        current_mode.value = panel_modes.search
        search()
      } else {
        search_result.value = []
        if (current_mode.value == panel_modes.search)
          current_mode.value = panel_modes.chat_list
      }
    })

    return {
      panel_modes, current_mode, menu_items, new_group_popup_visible, new_group_name, new_channel_popup_visible, new_channel_name, is_new_channel_private, search_query, search_result,
      openChat, searchResultHandler, createGroup, createChannel,
      getChatList, getSelectedChatId
    }
  }
}
</script>

<style scoped>
#selector {
  display: flex;
  flex-flow: column;
  flex: 1;
  height: 100%;
  padding: 0.5em 0em;
  box-shadow: 1px 1px 5px lightsteelblue;
}

#toolbar {
  display: flex;
  justify-content: space-between;
  padding: 0em 0.5em 0.5em 0.5em;
}

#search-field {
  flex: 1;
  width: 10em;
  margin-right: 1em;
  border-radius: 5px;
}
.empty-list-label {
  display: flex;
  justify-content: center;
  color: grey;
}
</style>
