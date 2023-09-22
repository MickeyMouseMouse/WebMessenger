<template>
  <div id='sign_up'>
    <div id='sign_up_panel'>
      <div style='position: absolute; top: 0.5em; right: 0.5em'>
        <span class='pi pi-question-circle' style='color: #0b7ad1; cursor: help' @click='showCredentialsRequirements' />
      </div>
      <div style='display: flex; flex-flow: column' @keydown.enter='signUp'>
        <div>
          <div style='display: flex; justify-content: center; padding-bottom: 0.5em'>
            <img v-if='image == null' id='photo' src='@/assets/blank_user_photo.jpg'>
            <img v-else id='photo' :src='image' />
          </div>
          <div style='display: flex; justify-content: center; align-items: center'>
            <input id='selectPhoto' accept='image/png,image/jpeg' type='file' @change='onFileChange'
              style='display: none' />
            <Button label='Browse' icon='pi pi-camera' class='p-button-raised p-button-rounded'
              @click='openFileChooser' />
            <Button icon='pi pi-trash' :disabled='image == null' style='margin-left: 0.5em'
              class='p-button-raised p-button-rounded p-button-danger'
              @click='resetPhoto' />
          </div>
        </div>
        <div style='margin-top: 1.5em'>
          <span class='p-float-label'>
            <InputText v-model='username' id='username' style='width: 14em'
              :class="{'p-invalid': !isUsernameValid}" />
            <label for='username'>Username</label>
          </span>
        </div>
        <div style='margin-top: 1.5em'>
          <span class='p-float-label'>
            <InputText v-model='login' id='login' style='width: 14em'
              :class="{'p-invalid': !isLoginValid}" />
            <label for='login'>Login</label>
          </span>
        </div>
        <div style='display: flex; align-items: center; margin-top: 1.5em'>
          <span class='p-float-label'>
            <Password v-model='password' id='password' :feedback='false' :toggleMask='true'
              :class="{'p-invalid': !isPasswordValid}" :inputStyle="{'width': '12.5em'}" />
            <label for='password'>Password</label>
          </span>
          <span class='pi pi-lock' style='margin-left: 0.4em; cursor: pointer'
            title='Generate a new password' @click='generatePassword' />
        </div>
        <div style='margin-top: 1.5em'>
          <span class='p-float-label'>
            <Password v-model='repeat_password' id='repeat-password' :feedback='false' :toggleMask='true'
              :class="{'p-invalid': !isRepeatPasswordValid}" :inputStyle="{'width': '14em'}" />
            <label for='repeat-password'>Repeat password</label>
          </span>
        </div>
      </div>
      <div style='display: flex; margin-top: 1em'>
        <div style='display: flex; flex: 1'>
          <Button label='Sign in instead' class='p-button-link' style='padding: 0.1em;' @click='signIn' />
        </div>
        <div>
          <Button label='Sign up' class='p-button-raised p-button-success' :disabled='!isCredentialsValid' @click='signUp' />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import makeHTTPRequest from '@/makeHTTPRequest'
export default {
	name: 'v-sign-up',
  setup() {
    const store = useStore()
    const router = useRouter()
    const toast = useToast()

    const photo_file = ref(null)
    const image = ref(null)
    const username = ref('')
    const login = ref('')
    const password = ref('')
    const repeat_password = ref('')

    function showCredentialsRequirements() {
      toast.add({severity: 'info', summary: 'Credentials requirements',
          detail: 'Username: min 2 chars, unique;\nLogin: min 4 chars, unique;\nPassword: min 8 chars, at least one lowercase, uppercase and numeric',})
    }

    function openFileChooser() {
      document.getElementById('selectPhoto').click()
    }

    function onFileChange(e) {
      let file = e.target.files[0]
      if (!file) return
      if (file.size <= 512 * 1024) {
        photo_file.value = file
        image.value = URL.createObjectURL(photo_file.value)
      } else {
        resetPhoto()
        toast.add({severity: 'error', summary: 'Inappropriate photo',
          detail: 'File is too big',
          life: 5000})
      }
    }

    function resetPhoto() {
      document.getElementById('selectPhoto').value = ''
      photo_file.value = null
      image.value = null
    }

    function generatePassword() {
      password.value = getPassword(6, 2, 2, 2)
      repeat_password.value = ''
    }

    function getPassword(lowercase, uppercase, numbers, other) {
      var chars = [
        'abcdefghijklmnopqrstuvwxy',
        'ABCDEFGHIJKLMNOPQRSTUVWXY',
        '0123456789',
        '!@#$%*()[]-_+=.'
      ]

      function randInt(this_max) { // return int between 0 and this_max - 1
        let umax = Math.pow(2, 32)
        let max = umax - (umax % this_max)
        let r = new Uint32Array(1)
        do {
          crypto.getRandomValues(r)
        } while(r[0] > max)
        return r[0] % this_max
      }

      function randCharFrom(chars) {
        return chars[randInt(chars.length)]
      }

      function shuffle(arr) {
        for (let i = 0, n = arr.length; i < n - 2; i++) {
            let j = randInt(n - i); // <-- required comma
            [arr[j], arr[i]] = [arr[i], arr[j]]
        }
        return arr
      }

      return shuffle([lowercase, uppercase, numbers, other].map(function(len, i) {
        return Array(len).fill(chars[i]).map(x => randCharFrom(x)).join('')
      }).concat().join('').split('')).join('')
    }

    const signIn = () => router.push({ path: '/' })

    async function signUp() {
      let r = await makeHTTPRequest('/sign_up', 'CREATE', {
        'username': username.value,
        'login': login.value,
        'password': password.value
      })
      if (r.status == 201) {
        await store.dispatch('connectSocketIO')
        if (photo_file.value) {
          store.getters.getSocket.emit('/settings/update_user_photo', {
            'name': photo_file.value.name,
            'data': photo_file.value
          })
        }
        router.replace({'path': '/account/messenger'})
      } else {
        toast.add({severity: 'error',
          summary: 'Registration failed',
          detail: await r.text(),
          life: 5000})
      }
    }

    const isUsernameValid = computed(() => username.value.length == 0 || username.value.length >= 2)

    const isLoginValid = computed(() => login.value.length == 0 || login.value.length >= 4)

    const isPasswordValid = computed(() => password.value.length == 0 || /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.{8,})/.test(password.value))

    const isRepeatPasswordValid = computed(() => repeat_password.value.length == 0 || password.value == repeat_password.value)

    const isCredentialsValid = computed(() =>
      username.value.length && isUsernameValid && 
      login.value.length && isLoginValid && 
      password.value.length && isPasswordValid &&
      repeat_password.value.length && isRepeatPasswordValid
    )

    return {
      photo_file, image, username, login, password, repeat_password,
      showCredentialsRequirements, openFileChooser, onFileChange, resetPhoto, generatePassword, signIn, signUp,
      isUsernameValid, isLoginValid, isPasswordValid, isRepeatPasswordValid, isCredentialsValid
    }
  }
}
</script>

<style scoped>
#sign_up {
  display: flex;
  flex-flow: column;
  flex: 1;
  align-items: center;
  padding-top: 2em;
  background-color: #edeef0;
  overflow: auto;
}

#sign_up_panel {
  position: relative;
  padding: 1em;
	background-color: white;
	box-shadow: 0px 0px 5px lightslategrey;
  border-radius: 5px;
}

#photo {
  border: 1px solid black;
  width: 100px;
  height: 100px;
}
</style>
