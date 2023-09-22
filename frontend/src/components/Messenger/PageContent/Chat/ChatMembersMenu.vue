<template>
  <div style='display: flex; flex-flow: column'>
    <span class='p-input-icon-right'>
      <i class='pi pi-times' style='cursor: pointer' @click="search_query = ''"/>
      <InputText id='search-field' v-model='search_query' placeholder='Search' />
    </span>
    <div style='overflow: auto'>
      <TabView v-model:activeIndex='menu_index' style='margin-top: 1em'>
        <TabPanel header='Users'>
          <ItemList :list='user_list' show_ownership
            :remove_btn=getSelectedChatInfo.is_owner @remove='removeUser'
            :filter='search_query' />
        </TabPanel>
        <TabPanel v-if='getSelectedChatInfo.is_owner' header='Add user'>
          <div v-show='search_result.length == 0' style='display: flex; justify-content: center; color: grey'>
            Find the user to add
          </div>
          <ItemList :list='search_result' add_btn @add='addUser'/>
        </TabPanel>
      </TabView>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
import ItemList from '@/components/ItemList.vue'
export default {
  name: 'v-chat-members-menu',
  components: {
    ItemList
  },
  setup() {
    const search_query = ref('')
    const menu_index = ref(0)
    const user_list = ref([])
    const search_result = ref([])

    const store = useStore()
    const toast = useToast()

    // on create
    store.getters.getSocket.emit('/messenger/get_chat_members', {
      'chat_id': store.getters.getSelectedChatId
    }, (r) => {
      if (r.status == 200) {
        user_list.value = r.chat_members
      }
    })

    function searchUser() {
      if (menu_index.value == 1) { // 'Add user' tab
        if (search_query.value.length == 0) {
          search_result.value = []
        } else {
          store.getters.getSocket.emit('/messenger/search_new_chat_member', {
            'chat_id': store.getters.getSelectedChatId,
            'query': search_query.value,
          }, (r) => {
            if (r.status == 200) {
              search_result.value = r.search_result
            }
          })
        }
      }
    }

    function addUser(user) {
      store.getters.getSocket.emit('/messenger/add_user_to_chat', {
        'user_id': user.id,
        'chat_id': store.getters.getSelectedChatId
      }, (r) => {
        if (r.status == 200) {
          search_result.value = search_result.value.filter((item) => item.id != user.id)
          user_list.value.splice(1, 0, user)
        } else if (r.status == 403) {
          toast.add({severity: 'error', detail: r.error, life: 5000})
        }
      })
    }

    function removeUser(user) {
      store.getters.getSocket.emit('/messenger/remove_user_from_chat', {
        'user_id': user.id,
        'chat_id': store.getters.getSelectedChatId
      }, (r) => {
        if (r.status == 200) {
          user_list.value = user_list.value.filter((item) => item.id != user.id)
        }
      })
    }

    const getSelectedChatInfo = computed(() => store.getters.getSelectedChatInfo)

    watch(search_query, () => searchUser())

    watch(menu_index, () => {
      search_query.value = ''
      search_result.value = []
    })

    return {
      search_query, menu_index, user_list, search_result,
      searchUser, addUser, removeUser,
      getSelectedChatInfo
    }
  }
}
</script>

<style scoped>

</style>
