<template>
  <div id='settings-page'>
    <div id='settings_content'>
      <div style='padding-bottom: 1em'>
        <div style='display: flex; justify-content: center; padding-bottom: 0.5em'>
          <img v-if='photo==null' id='photo' src='@/assets/blank_user_photo.jpg'>
          <img v-else id='photo' :src='photo' />
        </div>
        <div style='display: flex; justify-content: center; align-items: center'>
          <input id='selectPhoto' accept='image/png,image/jpeg' type='file' @change='onFileChange'
            style='display: none' />
          <Button label='Browse' icon='pi pi-camera' class='p-button-raised p-button-rounded'
            @click='openFileChooser' />
          <Button icon='pi pi-trash' :disabled='photo==null' style='margin-left: 0.5em'
            class='p-button-raised p-button-rounded p-button-danger'
            @click='resetPhoto' />
        </div>
      </div>
      <div class='setting'>
        <div style='margin-right: 0.2em'>
          Username:
        </div>
        <div style='width: 8em; text-align: center; border-bottom: 1px solid' :title='username'>
          <p style='overflow: hidden; text-overflow: ellipsis; margin: 0em'>
            {{username}}
            <Skeleton v-show='!username.length' style='padding: 0.6em 0em' />
          </p>
        </div>
        <Button class='p-button-text' icon='pi pi-pencil'
          @click='showChangeUsernameDialog' />
      </div>
      <div class='setting'>
        <div style='flex: 1'>Show my online status</div>
        <InputSwitch v-model='show_online_status' />
      </div>
      <div class='setting'>
        <Button class='p-button-link' label='Blocked users' style='padding: 0em'
          @click='blocked_users_menu_visible = true' />
      </div>
      <div class='setting'>
        <Button class='p-button-link' label='Change password' style='padding: 0em'
          @click='showChangePasswordDialog' />
      </div>
      <div class='setting'>
        <Button class='p-button-text p-button-danger' label='Delete account'
          style='padding: 0em'
          @click='showDeleteAccountDialog' />
      </div>
    </div>
  </div>

  <PopUp v-model:visible='change_username_popup_visible'
    header='Change username' :modal='true' :draggable='false'>
    <InputText v-model='new_username' placeholder='New username' autofocus
       @keydown.enter='changeUsername' />
    <template #footer>
      <Button label='Change' :disabled='new_username.length == 0'
        @click='changeUsername' />
    </template>
  </PopUp>

  <PopUp v-model:visible='blocked_users_menu_visible' @keydown.esc='blocked_users_menu_visible = false'
    header='Blocked users' :modal='true' :draggable='false' style='min-width: 16em; overflow: hidden'>
    <BlockedUsersMenu v-if='blocked_users_menu_visible' />
  </PopUp>

  <PopUp v-model:visible='change_password_popup_visible'
    header='Change password' :modal='true' :draggable='false'>
    <div style='display: flex; flex-flow: column' @keydown.enter='changePassword'>
      <Password v-model='current_password' style='margin-bottom: 0.5em'
        placeholder='Current password' :feedback='false' :toggleMask='true' />
      <Password v-model='new_password' style='margin-bottom: 0.5em'
        placeholder='New password' :feedback='false' :toggleMask='true' />
      <Password v-model='repeat_new_password' style='margin-bottom: 0.5em'
        placeholder='Repeat new password' :feedback='false' :toggleMask='true' />
    </div>
    <template #footer>
      <Button label='Change' :disabled='!current_password || !new_password || new_password != repeat_new_password'
        @click='changePassword' />
    </template>
  </PopUp>

  <PopUp v-model:visible='delete_account_popup_visible'
    header='Delete account' :modal='true' :draggable='false'>
    <div style='display: flex; flex-flow: column'>
      <div style='display: flex; justify-content: center'>
        <Password v-model='current_password' placeholder='Password'
          :feedback='false' :toggleMask='true' />
      </div>
      <div style='display: flex; align-items: center; margin-top: 2em'>
        <div style='flex: 1; margin-right: 1em; width: 16em'>
          I understand that my data stored on the server will be permanently deleted
        </div>
        <Checkbox v-model='agree' :binary='true' />
      </div>
    </div>
    <template #footer>
      <Button label='Delete' class='p-button-danger' :disabled='!agree' @click='deleteAccount' />
    </template>
  </PopUp>
</template>

<script>
import { ref, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import BlockedUsersMenu from './BlockedUsersMenu.vue'
import makeHTTPRequest from '@/makeHTTPRequest'
export default {
  name: 'v-settings-page',
  components: {
    BlockedUsersMenu
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const toast = useToast()

    const photo = ref(null)
    const username = ref('')
    const change_username_popup_visible = ref(false)
    const new_username = ref('')
    const show_online_status = ref(null)
    const blocked_users_menu_visible = ref(false)
    const change_password_popup_visible = ref(false)
    const current_password = ref('')
    const new_password = ref('')
    const repeat_new_password = ref('')
    const delete_account_popup_visible = ref(false)
    const agree = ref(false)

    // on create
    store.getters.getSocket.emit('/settings/get_user_info', (r) => {
      if (r.status == 200) {
        username.value = r.user_info.username
        show_online_status.value = r.user_info.show_online_status
        if (r.user_info.photo_data) {
          photo.value = URL.createObjectURL(new Blob([r.user_info.photo_data], {type: 'image/jpeg'}))
        } else {
          photo.value = null
        }
      }
    })

    function openFileChooser() {
      document.getElementById('selectPhoto').click()
    }

    function onFileChange(e) {
      let file = e.target.files[0]
      if (!file) return
      photo.value = URL.createObjectURL(file)
      store.getters.getSocket.emit('/settings/update_user_photo', {'name': file.name, 'data': file}, (r) => {
        if (r.status != 201) {
          photo.value = null
          toast.add({severity: 'error', summary: r.error, life: 5000})
        }
      })
    }

    function resetPhoto() {
      store.getters.getSocket.emit('/settings/delete_photo', () => {
        photo.value = null
        document.getElementById('selectPhoto').value = ''
      })
    }

    function changeUsername() {
      if (new_username.value.length < 2) {
        toast.add({
          severity: 'error',
          summary: 'Short username',
          detail: 'The username must consist at least of 2 characters',
          life: 5000
        })
        return
      }
      store.getters.getSocket.emit('/settings/update_username', {
        'new_username': new_username.value
      }, (r) => {
        if (r.status == 201) {
          username.value = new_username.value
        } else if (r.status == 409) {
          toast.add({severity: 'error',
            detail: 'This username already exists',
            life: 5000})
        }
      })
      change_username_popup_visible.value = false
    }

    function changePassword() {
      if (!checkPasswordSecurity()) return
      store.getters.getSocket.emit('/settings/update_password', {
        'current_password': current_password.value,
        'new_password': new_password.value
      }, (r) => {
        if (r.status == 201)
          toast.add({severity: 'info', summary: 'Password updated', life: 5000})
        else
          toast.add({severity: 'error', summary: r.error, life: 5000})
      })
      change_password_popup_visible.value = false
    }

    function checkPasswordSecurity() {
      let success = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.{8,})/.test(new_password.value)
      if (!success) {
        toast.add({severity: 'error', summary: 'Weak password',
          detail: 'The password must consist of at least 8 characters, at least one lowercase, one uppercase and one digit',
          life: 10000})
      }
      return success
    }

    async function deleteAccount() {
      store.getters.getSocket.emit('privilege_check', {
        'password': current_password.value
      }, async (r) => {
        if (r.status == 200) {
          store.dispatch('resetData')
          await makeHTTPRequest('/settings/delete_account', 'DELETE', {
            'password': current_password.value
          })
          router.replace({'path': '/'})
          toast.add({severity: 'info', summary: 'Account deleted', life: 5000})
        } else {
          toast.add({severity: 'error', summary: 'Wrong password', life: 5000})
        }
      })
      delete_account_popup_visible.value = false
    }

    function showChangeUsernameDialog() {
      new_username.value = username.value
      change_username_popup_visible.value = true
    }

    function showChangePasswordDialog() {
      current_password.value = ''
      new_password.value = ''
      repeat_new_password.value = ''
      change_password_popup_visible.value = true
    }

    function showDeleteAccountDialog() {
      current_password.value = ''
      agree.value = false
      delete_account_popup_visible.value = true
    }

    watch(show_online_status, (new_status, old_status) => {
      if (old_status != null) {
        store.getters.getSocket.emit('/settings/update_show_online_status', {
          'new_status': new_status
        })
      }
    })

    return {
      photo, username, change_username_popup_visible, new_username, show_online_status, blocked_users_menu_visible, change_password_popup_visible, current_password, new_password, repeat_new_password, delete_account_popup_visible, agree,
      openFileChooser, onFileChange, resetPhoto, changeUsername, changePassword, deleteAccount, showChangeUsernameDialog, showChangePasswordDialog, showDeleteAccountDialog
    }
  }
}
</script>

<style scoped>
#settings-page {
  display: flex;
  justify-content: center;
  flex: 1;
  margin: 1em;
  overflow: auto;
}

#photo {
  border: 1px solid black;
  width: 100px;
  height: 100px;
}

.setting {
  display: flex;
  align-items: center;
  margin-bottom: 1em;
}
</style>
