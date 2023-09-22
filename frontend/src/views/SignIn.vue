<template>
  <div id='sign_in'>
    <div id='sign_in_panel'>
      <div style='display: flex; flex-flow: column' @keydown.enter='signIn'>
        <form>
          <div style='margin-top: 1.5em'>
            <span class='p-float-label'>
              <InputText v-model='login' id='login' name='email' type='email' autocomplete='username'
                style='width: 14em' autofocus />
              <label for='login'>Login</label>
            </span>
          </div>
          <div style='margin-top: 1.5em'>
            <span class='p-float-label'>
              <Password v-model='password' id='password' name='password' type='password' autocomplete='current-password'
                :inputStyle="{'width': '14em'}" :toggleMask='true' :feedback='false' />
              <label for='password'>Password</label>
            </span>
          </div>
        </form>
      </div>
      <div style='display: flex; margin-top: 1em'>
        <div style='display: flex; flex: 1'>
          <Button label='Sign Up' class='p-button-link' style='padding: 0.1em; color: #689F38'
            @click='signUp'/>
        </div>
        <div>
          <Button label='Sign In' class='p-button-raised'
            :disabled="login == '' || password == ''" @click="signIn" />
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
	name: 'v-sign-in',
  setup() {
    const store = useStore()
    const router = useRouter()
    const toast = useToast()

    const login = ref('12345')
    const password = ref('Qwerty67')

    async function signIn() {
      let r = await makeHTTPRequest('/sign_in', 'POST', {
        'login': login.value,
        'password': password.value
      })
      if (r.status == 200) {
        await store.dispatch('connectSocketIO')
        router.replace({'path': '/account/messenger'})
      } else if (r.status == 401) {
        toast.add({severity: 'error', summary: 'Authentication failed',
          detail: 'Invalid username or password', life: 5000})
        login.value = ''
        password.value = ''
      }
    }

    const signUp = () => router.push({ path: '/signup' })

    const getSocketError = computed(() => store.getters.getSocketError)

    return {
      login, password,
      signIn, signUp,
      getSocketError
    }
  }
}
</script>

<style scoped>
#sign_in {
  display: flex;
  flex-flow: column;
  flex: 1;
  align-items: center;
  padding-top: 4em;
  background-color: #edeef0;
}

#sign_in_panel {
  padding: 1em;
	background-color: white;
	box-shadow: 0px 0px 5px lightslategrey;
  border-radius: 5px;
}
</style>
