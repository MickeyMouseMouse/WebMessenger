<template>
  <div id='files-page'>
    <div style='display: flex; margin-bottom: 0.5em; padding: 0.2em'>
      <Breadcrumb :path='current_working_dir' @goTo='goTo' />
      <div style='margin-left: 0.5em'>
        <Button icon='pi pi-bars' class='p-button-rounded p-button-outlined' @click='(e) => $refs.menu.toggle(e)' />
        <Menu ref='menu' :model='menu_items' :popup='true' />
        <input id='selectFile' type='file' @change='onFileChange' style='display: none' />
      </div>
    </div>
    <div id='file_container'>
      <div style='display: flex; flex-flow: column; flex: 1; overflow-x: hidden; overflow-y: auto;'>
        <div v-if='total == 0' style='display: flex; justify-content: center; margin-top: 1em; color: grey'>
          This folder is empty
        </div>
        <FileItem v-else v-for='item in content' :key='item.id'
          :type='item.type' :filename='item.name' :cwd='current_working_dir' :size='item.size' 
          @openDir='openDir' @cut='cutItem' @copy='copyItem' @reload='fetchDirContent(); fetchFreeSpace()' />
      </div>
      <div style='display: flex; justify-content: space-between; margin-top: 0.2em; color: grey'>
        <div v-if='total <= items_on_page'>
          Items: {{ total.value  }}
        </div>
        <div v-else>
          Items: {{ content.value.length }}/{{ total.value }}
        </div>
        <div v-show='free_space'>
          Free: {{ free_space.value }} GB
        </div>
      </div>
    </div>
    <Paginator v-model:first='paginator' :rows='items_on_page' :totalRecords='total' />
  </div>

  <PopUp v-model:visible='create_new_dir_popup_visible'
    header='Create folder' :modal='true' :draggable='false'>
    <InputText v-model='new_dir_name' placeholder='Name' autofocus @keydown.enter='createNewDir'/>
    <template #footer>
      <Button label='Create' :disabled='new_dir_name.length == 0' @click='createNewDir' />
    </template>
  </PopUp>
</template>

<script>
import { ref, onBeforeUnmount, watch } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
import Breadcrumb from '@/components/Files/Breadcrumb.vue'
import FileItem from '@/components/Files/FileItem.vue'
export default {
  name: 'v-files-page',
  components: {
    Breadcrumb,
    FileItem
  },
  setup() {
    const store = useStore()
    const toast = useToast()

    const current_working_dir = ref(store.getters.getCurrentWorkingDir)
    const menu_items = [
      {
        icon: 'pi pi-plus',
        label: 'Upload file',
        command: () => { // open file chooser
          document.getElementById('selectFile').click()
        }
      },
      {
        icon: 'pi pi-folder',
        label: 'Create folder',
        command: () => {
          new_dir_name.value = ''
          create_new_dir_popup_visible.value = true
        }
      },
      {
        visible: () => item.value != null,
        icon: 'pi pi-file',
        label: 'Paste',
        command: () => {
          pasteItem()
        }
      }
    ]
    const new_dir_name = ref('')
    const create_new_dir_popup_visible = ref(false)
    const item = ref(null)
    const content = ref([])
    const paginator = ref(store.getters.getPaginator)
    const items_on_page = ref(0)
    const total = ref(0)
    const free_space = ref('')

    // on create
    fetchDirContent()
    fetchFreeSpace() 

    onBeforeUnmount(() => {
      store.dispatch('setCurrentWorkingDir', current_working_dir.value)
      store.dispatch('setPaginator', paginator.value)
    })

    function fetchDirContent() {
      store.getters.getSocket.emit('/files/get_directory_content', {
        'cwd': current_working_dir.value.join('/'), 'paginator': paginator.value
      }, (r) => {
        if (r.status == 200) {
          content.value = r.content
          items_on_page.value = r.items,
          total.value = r.total
        }
      })
    }

    function fetchFreeSpace() {
      store.getters.getSocket.emit('/files/get_free_space', {
        'cwd': current_working_dir.value.join('/'),
      }, (r) => {
        if (r.status == 200) {
          free_space.value = r.free_space
        }
      })
    }

    function onFileChange(e) {
      let file = e.target.files[0]
      if (!file) return
      store.getters.getSocket.emit('/files/upload', {
        'cwd': current_working_dir.value.join('/'),
        'file_name': file.name,
        'file_data': file
      }, (r) => {
        if (r.status == 200) {
          fetchDirContent()
          fetchFreeSpace()
        } else {
          toast.add({severity: 'error', summary: 'Failed',
            detail: r.error, life: 5000})
        }
      })
    }

    function goTo(path) {
      current_working_dir.value = path
      if (paginator.value == 0) {
        fetchDirContent()
      } else {
        paginator.value = 0 // watcher trigger
      }
    }

    function openDir(dirName) {
      current_working_dir.value.push(dirName)
      if (paginator.value == 0) {
        fetchDirContent()
      } else {
        paginator.value = 0 // watcher trigger
      }
    }

    function createNewDir() {
      store.getters.getSocket.emit('/files/create_dir', {
        'cwd': current_working_dir.value.join('/'),
        'name': new_dir_name.value
      }, (r) => {
        if (r.status == 200) {
          fetchDirContent()
          create_new_dir_popup_visible.value = false
        } else {
          toast.add({severity: 'error', summary: 'Failed',
            detail: r.error, life: 5000})
        }
      })
    }

    function cutItem(name) {
      item.value = {
        mode: 'move',
        path: current_working_dir.value.join('/'),
        name: name
      }
    }

    function copyItem(name) {
      item.value = {
        mode: 'copy',
        path: current_working_dir.value.join('/'),
        name: name
      }
    }
    
    function pasteItem() {
      if (item.value == null) return
      store.getters.getSocket.emit('/files/' + item.value.mode, {
        cwd: item.value.path,
        name: item.value.name,
        dest: current_working_dir.value.join('/')
      }, (r) => {
        if (r.status == 200) {
          fetchDirContent()
          fetchFreeSpace()
        } else {
          toast.add({severity: 'error', summary: 'Failed', detail: r.error, life: 5000})
        }
      })
      item.value = null
    }

    watch(paginator, () => fetchDirContent())

    return {
      current_working_dir, menu_items, new_dir_name, create_new_dir_popup_visible, item, content, paginator, items_on_page, total, free_space,
      fetchDirContent, fetchFreeSpace, onFileChange, goTo, openDir, createNewDir, cutItem, copyItem, pasteItem
    }
  }
}
</script>

<style scoped>
#files-page {
  display: flex;
  flex-flow: column;
  flex: 1;
  margin: 0.5em;
  overflow: auto;
}

#file_container {
  display: flex;
  flex-flow: column;
  flex: 1;
  padding: 0.4em;
  border: 1px solid steelblue;
  border-radius: 5px;
  box-shadow: inset 0px 0px 5px 1px lightsteelblue;
  overflow: auto;
}
</style>
