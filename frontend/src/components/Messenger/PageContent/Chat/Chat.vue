<template>
  <div id='chat'>
    <div v-show='isChatOpen' style='display: flex'>
      <div style='display: flex; flex: 1'>
        <Button class='p-button-rounded p-button-outlined'
          :icon="isDesktop ? 'pi pi-times' : 'pi pi-chevron-left'"
          @click='closeChat' />
      </div>
      <div style='display: flex; align-items: center'>
        {{ getSelectedChatInfo.name }}
        <div v-show='getSelectedChatInfo.online' title='Online' style='display: flex; align-items: center; margin-left: 0.5em'>
          <div style='width: 0.5em; height: 0.5em; border-radius: 90px; background-color: green' />
        </div>
      </div>
      <div style='display: flex; flex: 1; justify-content: end;'>
        <Button class='p-button-rounded p-button-outlined' icon='pi pi-ellipsis-h'
          @click='(e) => $refs.chatMenu.toggle(e)' />
        <Menu ref='chatMenu' :model='chatMenuItems' :popup='true' />
      </div>
    </div>
    <div id='middle'>
      <div v-show='!isChatOpen' style='display: flex; flex: 1; justify-content: center; align-items: center'>
        <div style='color: grey; background-color: whitesmoke; padding: 0.5em 1em; border-radius: 30px; text-align: center;'>
          Select a chat to start messaging
        </div>
     </div>
      <div v-show='isChatOpen' style='display: flex; flex: 1'>
        <Menu ref='messageMenu' :model='message_menu_items' :popup='true' />
        <div v-if='message_list.length == 0' style='display: flex; flex: 1; justify-content: center; align-items: center'>
          <div style='color: grey; text-align: center;'>
            There are no messages here yet
          </div>
        </div>
        <div v-else style='display: flex; flex-flow: column; flex: 1'>
          <div v-for='message_id in message_list' :key='message_id.id' class='list_row'>
            <div :class="['message_container', {'flex_container_right': getMessages[message_id].is_my_message}]">
              <div class='message_wrapper'>
                <div style='display: flex; margin-bottom: 0.2em; color: grey; font-size: x-small;'
                  :class="{'flex_container_right': getMessages[message_id].is_my_message}">
                  <div v-show='!getMessages[message_id].is_my_message' style='margin-right: 0.2em'>
                    {{ getMessages[message_id].author }},
                  </div>
                  <div>
                    {{ getDate(getMessages[message_id].timestamp) }}
                  </div>
                </div>
                <div style='display: flex' :class="{'flex_container_right': getMessages[message_id].is_my_message}">
                  <div :class="['message_panel', getMessages[message_id].is_my_message ? 'message_panel_right' : 'message_panel_left']">
                    <div>
                      {{ getMessages[message_id].text }}
                    </div>
                    <div v-if='getMessages[message_id].is_my_message' class='pi pi-ellipsis-v'
                      style='display: flex; align-items: end; margin-left: 0.5em; font-size: 0.7rem; cursor: pointer'
                      @click='(e) => {$refs.messageMenu.toggle(e); selected_message_id = message_id}' />
                  </div>
                </div>
              </div>
            </div>
            <div v-if='message_id == last_message_read_id_on_chat_opening'
              style='display: flex; align-items: center; color: grey'>
              <div style='flex: 1; border-bottom: 1px solid grey' />
              <div style='padding: 0em 0.5em'>Unread Messages</div>
              <div style='flex: 1; border-bottom: 1px solid grey' />
            </div>
          </div>
        </div>
      </div>
      <div id='scrollToMe' />
    </div>
    <div v-show="isChatOpen && !(getSelectedChatInfo.type=='channel' && !getSelectedChatInfo.is_owner)" id='bottom'>
      <div style='display: flex; align-items: end'>
        <Button class='p-button-text' icon='pi pi-paperclip' />
      </div>
      <div id='input-field' placeholder='Message' contenteditable autofocus
        oninput="if (this.innerHTML.trim()==='<br>') this.innerHTML=''" />
      <div style='display: flex; align-items: end'>
        <Button class='p-button-text' icon='pi pi-send' @click='send' />
        <Button v-show='message_editing' class='p-button-text' icon='pi pi-times' @click='cancelMessageEditing' />
      </div>
    </div>

    <PopUp v-model:visible='rename_popup_visible' @keydown.esc='rename_popup_visible = false'
      header='Rename' :modal='true' :draggable='false'>
      <InputText v-model='new_name' placeholder='Name' />
      <template #footer>
        <Button label='Rename' :disabled='new_name == getSelectedChatInfo.name' @click='renameChat' />
      </template>
    </PopUp>
    <PopUp v-model:visible='chat_members_menu_visible' @keydown.esc='chat_members_menu_visible = false'
      header='Members' :modal='true' :draggable='false' style='min-width: 16em; overflow: hidden'>
      <ChatMembersMenu v-if='chat_members_menu_visible' />
    </PopUp>
    <PopUp v-model:visible='leave_popup_visible' @keydown.esc='leave_popup_visible = false'
      header='Leave' :modal='true' :draggable='false'>
      Are you sure you want to leave?
      <template #footer>
        <Button label='No' icon='pi pi-times' class='p-button-text'
          @click='leave_popup_visible = false' />
        <Button label='Yes' icon='pi pi-check' autofocus @click='leaveChat' />
      </template>
    </PopUp>
    <PopUp v-model:visible='delete_popup_visible' @keydown.esc='delete_popup_visible = false'
      header='Delete' :modal='true' :draggable='false'>
      Are you sure you want to delete this chat?
      <template #footer>
        <Button label='No' icon='pi pi-times' class='p-button-text'
          @click='delete_popup_visible = false' />
        <Button label='Yes' icon='pi pi-check' autofocus @click='deleteChat' />
      </template>
    </PopUp>
  </div>
</template>

<script>
import { ref, onBeforeUpdate, onUpdated, computed, watch, nextTick } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
import ChatMembersMenu from './ChatMembersMenu.vue'
export default {
  name: 'v-chat',
  components: {
    ChatMembersMenu
  },
  setup() {
    const store = useStore()
    const toast = useToast()

    onBeforeUpdate(() => {
      let middle = document.getElementById('middle')
      let position = middle.scrollTop / (middle.scrollHeight - middle.innerHeight)
      if (!position || position >= 1) autoscroll_to_new_message.value = true
    })

    onUpdated(() => {
      if (isChatOpen.value) {
        if (autoscroll_to_new_message.value) {
          scrollToBottom('smooth')
          autoscroll_to_new_message.value = false
        }
        if (message_list.value.length) {
          let last_message_read_id = message_list.value.at(-1)
          if (last_message_read_id > getSelectedChatInfo.value.last_message_read_id) {
            store.getters.getSocket.emit('/messenger/set_last_message_read', {
              'chat_id': getSelectedChatId.value,
              'message_id': last_message_read_id
            }, (r) => {
              if (r.status == 200) {
                getSelectedChatInfo.value.last_message_read_id = last_message_read_id
                getSelectedChatInfo.value.unread_counter = 0
              }
            })
          }
        }
      }
    })

    const message_list = ref([])
    const last_message_read_id_on_chat_opening = ref(null)
    const autoscroll_to_new_message = ref(false)

    const chatMenuItems = [
      {
        visible: () => getSelectedChatInfo.value.type == 'dialog',
        icon: 'pi pi-phone',
        label: 'Call',
        command: () => {
          //call(getSelectedChatId.value)
        }
      },
      {
        visible: () => getSelectedChatInfo.value.type != 'dialog' && getSelectedChatInfo.value.is_owner,
        icon: 'pi pi-pencil',
        label: 'Rename',
        command: () => {
          new_name.value = getSelectedChatInfo.value.name
          rename_popup_visible.value = true
        }
      },
      {
        visible: () => getSelectedChatInfo.value.type == 'group' ||
            (getSelectedChatInfo.value.type == 'channel' && getSelectedChatInfo.value.is_private),
        icon: 'pi pi-users',
        label: 'Members',
        command: () => {
          chat_members_menu_visible.value = true
        }
      },
      {
        visible: () => getSelectedChatInfo.value.type == 'channel' && !getSelectedChatInfo.value.is_joined,
        icon: 'pi pi-sign-in',
        label: 'Join',
        command: () => {
          joinChat()
        }
      },
      {
        visible: () => getSelectedChatInfo.value.is_owner,
        separator: true
      },
      {
        visible: () => !getSelectedChatInfo.value.is_owner && (getSelectedChatInfo.value.type == 'group' ||
          (getSelectedChatInfo.value.type == 'channel' && getSelectedChatInfo.value.is_joined)),
        icon: 'pi pi-sign-out',
        label: 'Leave',
        command: () => {
          leave_popup_visible.value = true
        }
      },
      {
        visible: () => getSelectedChatInfo.value.type == 'dialog' || 
          (getSelectedChatInfo.value.type != 'dialog' && getSelectedChatInfo.value.is_owner),
        icon: 'pi pi-trash',
        label: 'Delete',
        command: () => {
          delete_popup_visible.value = true
        }
      }
    ]

    const new_name = ref('')
    
    const rename_popup_visible = ref(false)
    const chat_members_menu_visible = ref(false)
    const leave_popup_visible = ref(false)
    const delete_popup_visible = ref(false)

    const message_menu_items = [
      {
        icon: 'pi pi-pencil',
        label: 'Edit',
        command: () => {
          message_editing.value = true
          document.getElementById('input-field').innerText = getMessages[selected_message_id.value].text
        }
      },
      {
        icon: 'pi pi-trash',
        label: 'Delete',
        command: () => {
          deleteMessage()
        }
      }
    ]
    const selected_message_id = ref(null)
    const message_editing = ref(false)

    function closeChat() {
      if (getSelectedChatInfo.value.type == 'dialog' && getMessages.value.length == 0) {
        store.getters.getSocket.emit('/messenger/delete_chat', {
          'chat_id': getSelectedChatId.value
        })
      }
      store.dispatch('resetChat')
    }

    function renameChat() {
      if (new_name.value == getSelectedChatInfo.value.name) return
      store.getters.getSocket.emit('/messenger/rename_chat', {
        'chat_id': getSelectedChatId.value,
        'name': new_name.value
      }, (r) => {
        if (r.status == 200) {
          rename_popup_visible.value = false
        }
      })
    }

    function joinChat() {
      store.getters.getSocket.emit('/messenger/join_chat', {
        'chat_id': getSelectedChatId.value
      })
    }

    function leaveChat() {
      store.getters.getSocket.emit('/messenger/leave_chat', {
        'chat_id': getSelectedChatId.value
      }, (r) => {
        if (r.status == 200) {
          leave_popup_visible.value = false
          closeChat()
        }
      })
    }

    function deleteChat() {
      store.getters.getSocket.emit('/messenger/delete_chat', {
        'chat_id': getSelectedChatId.value
      }, (r) => {
        if (r.status == 200) {
          delete_popup_visible.value = false
          closeChat()
        }
      })
    }

    function scrollToBottom(mode = 'instant') { // smooth
      nextTick(() => {
        document.getElementById('scrollToMe').scrollIntoView({behavior: mode})
      })
    }

    function send() {
      let input = document.getElementById('input-field')
      let msg = input.innerText
      if (msg.length == 0) return

      if (message_editing.value) { // edit message
        store.getters.getSocket.emit('/messenger/edit_message', {
          'message_id': selected_message_id.value,
          'new_text': document.getElementById('input-field').innerText
        })
        message_editing.value = false
      } else { // send new message
        store.getters.getSocket.emit('/messenger/post_message', {
          'chat_id': getSelectedChatId.value,
          'type': 1, // text message
          'text': msg
        }, (r) => {
          if (r.status == 403) {
            toast.add({severity: 'error', detail: r.error, life: 5000})
          }
        })
      }
      input.innerText = ''
    }

    function cancelMessageEditing() {
      message_editing.value = false
      document.getElementById('input-field').innerText = ''
    }

    function deleteMessage() {
      store.getters.getSocket.emit('/messenger/delete_message', {
        'message_id': selected_message_id.value
      })
    }

    function getDate(timestamp) {
      let date = new Date(1000 * timestamp)
      return `${date.getHours()}:${date.getMinutes()} ${date.toLocaleDateString()}`
    }

    const isDesktop = computed(() => store.getters.isDesktop)

    const isChatOpen = computed(() => store.getters.isChatOpen)

    const getSelectedChatId = computed(() => store.getters.getSelectedChatId)

    const getSelectedChatInfo = computed(() => store.getters.getSelectedChatInfo)

    const getMessages = computed(() => store.getters.getMessages)

    watch(() => store.getters.getSelectedChatId, () => {
      if (store.getters.getSelectedChatInfo.unread_counter) {
        last_message_read_id_on_chat_opening.value = store.getters.getSelectedChatInfo.last_message_read_id
      } else {
        last_message_read_id_on_chat_opening.value = null
      }
      scrollToBottom() // auto scroll to chat bottom
    })

    watch(() => store.getters.getMessageList, (new_message_list) => {
      message_list.value = new_message_list
    })
    
    return {
      message_list, last_message_read_id_on_chat_opening, autoscroll_to_new_message, chatMenuItems, new_name, rename_popup_visible, chat_members_menu_visible, leave_popup_visible, delete_popup_visible, message_menu_items, selected_message_id, message_editing,
      closeChat, renameChat, joinChat, leaveChat, deleteChat, scrollToBottom, send, cancelMessageEditing, deleteMessage, getDate,
      isDesktop, isChatOpen, getSelectedChatInfo, getMessages
    }
  }
}
</script>

<style scoped>
#chat {
  display: flex;
  flex-flow: column;
  flex: 1;
  padding: 0.5em;
}

#middle {
  display: flex;
  flex-flow: column;
  flex: 1;
  padding: 0em 0.2em;
  margin: 0.2em 0em;
  overflow: auto;
}

.list_row {
  display: flex;
  flex-flow: column;
  margin: 0.5em 0em;
}

.message_container {
  display: flex;
}

.flex_container_right {
  justify-content: end;
}

.message_wrapper {
  display: flex;
  flex-flow: column;
}

.message_panel {
  display: flex;
  border-bottom-right-radius: 10px;
  border-bottom-left-radius: 10px;
  padding: 0.7em;
  overflow-wrap: break-word;
  word-break: break-all;
  white-space: pre-line;
}

.message_panel_left {
  border-top-right-radius: 10px;
  background-color: #ebebeb;
}

.message_panel_right {
  border-top-left-radius: 10px;
  background-color: #dbf1ff;
}

#bottom {
  display: flex;
  max-height: 30%;
}

#input-field {
  flex: 1;
  border: 1px solid black;
  border-radius: 0.3em;
  padding: 0.3em;
  overflow: auto;
}

#input-field:empty:before {
  content: attr(placeholder);
  color: gray;
}
</style>
