<template>
  <div style='display: flex; flex-flow: column'>
    <span class='p-input-icon-right'>
      <i class='pi pi-times' style='cursor: pointer' @click="search_query = ''" />
      <InputText id='search-field' v-model='search_query' placeholder='Search' />
    </span>
    <div style='overflow: auto'>
      <TabView v-model:activeIndex='menu_index' style='margin-top: 1em'>
        <TabPanel header='Users'>
          <ItemList :list='user_list' :filter='search_query' remove_btn @remove='removeUser' />
        </TabPanel>
        <TabPanel header='Add user'>
          <div v-show='search_result.length == 0' style='display: flex; justify-content: center; color: grey'>
            Find the user to block
          </div>
          <ItemList :list='search_result' add_btn @add='addUser'/>
        </TabPanel>
      </TabView>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { useStore } from 'vuex'
import ItemList from '@/components/ItemList.vue'
export default {
  name: 'v-blocked-users-menu',
  components: {
    ItemList
  },
  setup() {
    const search_query = ref('')
    const menu_index = ref(0)
    const user_list = ref([])
    const search_result = ref([])

    const store = useStore()

    // on create
    store.getters.getSocket.emit('/settings/get_blocked_users', (r) => {
      if (r.status == 200) {
        user_list.value = r.blocked_users
      }
    })

    function searchUser() {
      if (menu_index.value == 1) { // 'Add user' tab
        if (search_query.value.length == 0) {
          search_result.value = []
        } else {
          store.getters.getSocket.emit('/settings/search_user_to_block', {
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
      store.getters.getSocket.emit('/settings/block_user', {
        'user_id': user.id
      }, (r) => {
        if (r.status == 200) {
          search_result.value = search_result.value.filter((item) => item.id != user.id)
          user_list.value.splice(1, 0, user)
        }
      })
    }

    function removeUser(user) {
      store.getters.getSocket.emit('/settings/unblock_user', {
        'user_id': user.id
      }, (r) => {
        if (r.status == 200) {
          user_list.value = user_list.value.filter((item) => item.id != user.id)
        }
      })
    }

    watch(search_query, () => searchUser())

    watch(menu_index, () => {
      search_query.value = ''
      search_result.value = []
    })

    return {
      search_query, menu_index, user_list, search_result,
      searchUser, addUser, removeUser
    }
  }
}
</script>
  
<style scoped>

</style>
  