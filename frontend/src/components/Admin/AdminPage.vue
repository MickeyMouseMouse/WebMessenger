<template>
  <div id='admin-panel'>
    <div style='flex: 1; position: relative; overflow: hidden; margin: 0.5em'>
      <Terminal id='terminal'
        welcomeMessage='You should be CAREFUL and THINK what you are doing!'
        prompt='>'
        :key='component_key'
        @keyup.up='history_up' @keyup.down='history_down' />
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import Terminal from 'primevue/terminal'
import TerminalService from 'primevue/terminalservice'
export default {
    name: 'v-admin-panel',
    components: {
      Terminal
    },
    setup() {
      onMounted(() => TerminalService.on('command', commandHandler))

      onBeforeUnmount(() => TerminalService.off('command', commandHandler))

      const store = useStore()
      const router = useRouter()

      const component_key = ref(0)
      const history = ref([])
      const history_index = ref(0)

      function commandHandler(cmd) {
        history.value.push(cmd)
        history_index.value = history.value.length

        if (cmd == 'exit') {
          exit()
        } else if (cmd == 'clear') {
          component_key.value += 1
        } else {
          store.getters.getSocket.emit('/admin/cli', {'cmd': cmd}, (r) => {
            if (r.status == 200) {
              TerminalService.emit('response', r.output)
            } else {
              exit()
            }
          })
        }
      }

      const exit = () => router.replace({'path': '/account/messenger'})

      function history_up() {
        let input = document.getElementsByClassName('p-terminal-input')[0]
        if (history_index.value - 1 >= 0)
          input.value = history.value[--history_index.value]
      }

      function history_down() {
        let input = document.getElementsByClassName('p-terminal-input')[0]
        if (history_index.value + 1 < history.value.length)
          input.value = history.value[++history_index.value]
      }

      return {
        component_key, history, history_index,
        commandHandler, history_up, history_down
      }
    }
}
</script>

<style scoped>
#admin-panel {
  display: flex;
  flex-flow: column;
  flex: 1;
  padding: 0.5em;
}

#terminal {
  position: absolute;
  height: 100%;
  width: 100%;
  background-color: black;
  color: white;
  word-break: break-all;
  white-space: pre-line;
}
</style>