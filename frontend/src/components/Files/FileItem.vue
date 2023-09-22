<template>
  <div :class="['item', type=='file' ? 'file' : 'dir']">
    <div :class="type=='file' ? 'pi pi-file' : 'pi pi-folder'" style='margin-left: 0.5em' />
    <div class='item-name' @click='clickHandler' >
      <div style='position: absolute; width: 100%'>
        <p style='overflow: hidden; text-overflow: ellipsis;'>
          {{ filename }}
        </p>
      </div>
    </div>
    <Button icon='pi pi-ellipsis-v' class='p-button-text' @click='(e) => $refs.menu.toggle(e)' />
    <Menu ref='menu' :model='menu_items' :popup='true' />
  </div>

  <PopUp v-model:visible='rename_popup_visible'
    header='Rename' :modal='true' :draggable='false'>
    <InputText id='item-rename-field' v-model='new_name' placeholder='New name' autofocus @keydown.enter='rename' />
    <template #footer>
      <Button label='Rename' :disabled='new_name.length == 0' @click='rename' />
    </template>
  </PopUp>

  <PopUp v-model:visible='properties_popup_visible'
    header='Properties' :modal='true' :draggable='false'>
    <div style='display: flex; justify-content: center; min-width: 15em'>
      <div style='display: flex;'>
        <div style='display: flex; flex-flow: column; font-weight: bold;'>
          <div>Type:</div>
          <div>Name:</div>
          <div>Path:</div>
          <div>Size:</div>
        </div>
        <div style='display: flex; flex-flow: column; padding-left: 0.5em'>
          <div v-if="type=='dir'">Directory</div>
          <div v-else>File</div>
          
          <div>{{ filename }}</div>
          
          <div>{{ '/' + cwd.join('/') }}</div>
          
          <div v-if='size'>{{ size }} bytes</div>
          <div v-else>-</div>
        </div>
      </div>
    </div>
    <template #footer>
      <Button label='Ok' @click='properties_popup_visible = false' />
    </template>
  </PopUp>

  <PopUp v-model:visible='delete_popup_visible'
    header='Delete' :modal='true' :draggable='false' style='min-width: 15em'>
      Delete '{{name}}'?
    <template #footer>
      <Button label='Delete' class='p-button-danger' @click='deleteItem' />
    </template>
  </PopUp>
</template>

<script>
import { ref } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
export default {
  name: 'v-file-item',
  props: {
    type: String,
    filename: String,
    cwd: Array,
    size: Number
  },
  setup(props, {emit}) {
    const store = useStore()
    const toast = useToast()

    const menu_items = ref([
        {
          visible: () => props.type == 'file',
          icon: 'pi pi-download',
          label: 'Download',
          command: () => {
            download()
          }
        },
        {
          visible: () => props.type == 'dir',
          label: 'Open',
          icon: 'pi pi-folder-open',
          command: () => {
            clickHandler()
          }
        },
        {
          icon: 'pi pi-pencil',
          label: 'Rename',
          command: () => {
            new_name.value = props.filename
            rename_popup_visible.value = true
          }
        },
        {
          icon: 'pi pi-file-export',
          label: 'Cut',
          command: () => {
            emit('cut', props.filename)
          }
        },
        {
          icon: 'pi pi-copy',
          label: 'Copy',
          command: () => {
            emit('copy', props.filename)
          }
        },
        {
          icon: 'pi pi-info-circle',
          label: 'Properties',
          command: () => {
            properties_popup_visible.value = true
          }
        },
        {
          separator: true
        },
        {
          icon: 'pi pi-trash',
          label: 'Delete',
          command: () => {
            delete_popup_visible.value = true
          }
        }
    ])
    const rename_popup_visible = ref(false)
    const new_name = ref('')
    const properties_popup_visible = ref(false)
    const delete_popup_visible = ref(false)

    function clickHandler() {
      if (props.type == 'dir') {
        emit('openDir', props.filename)
      }
    }

    function download() {
      store.getters.getSocket.emit('/files/download', {
        'cwd': props.cwd.join('/'),
        'name': props.filename
      }, (r) => {
        if (r.status == 200) {
          let a = document.createElement('a')
          let file = new Blob([r.file_data], {type: 'application/octet-stream'})
          let url = window.URL.createObjectURL(file)
          a.href = url
          a.download = props.filename
          a.click()
          URL.revokeObjectURL(url)
        }
      })
    }

    function rename() {
      store.getters.getSocket.emit('/files/rename', {
        'cwd': props.cwd.join('/'),
        'name': props.filename,
        'new_name': new_name.value
      }, (r) => {
        if (r.status == 200) {
          emit('reload')
          rename_popup_visible.value = false
        } else {
          toast.add({severity: 'error', summary: 'Failed',
            detail: r.error, life: 5000})
        }
      })
    }

    function deleteItem() {
      store.getters.getSocket.emit('/files/delete', {
        'cwd': props.cwd.join('/'),
        'name': props.filename
      }, (r) => {
        if (r.status == 200) {
          emit('reload')
          delete_popup_visible.value = false
        } else {
          toast.add({severity: 'error', summary: 'Failed',
            detail: r.error, life: 5000})
        }
      })
    }

    return {
      menu_items, rename_popup_visible, new_name, properties_popup_visible, delete_popup_visible,
      clickHandler, rename, deleteItem
    }
  }
}
</script>

<style scoped>
.item {
  display: flex;
  align-items: center;
  min-height: 3em;
  max-height: 3em;
  margin: 0.25em;
  padding: 0.2em;
  cursor: pointer;
}

.file {
  border: 0.05em solid grey;
}

.file:hover {
  background-color: whitesmoke;
  transition: 100ms;
}

.dir {
  border: 0.1em solid black;
  border-radius: 5px;
}

.dir:hover {
  background-color: whitesmoke;
  transition: 100ms;
}

.item-name {
  display: flex;
  flex: 1;
  align-items: center;
  position: relative;
  height: 100%;
  padding-left: 1em
}
</style>