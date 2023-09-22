<template>
  <div id='breadcrumb'>
    <div style='margin-right: 0.5em'>
      <Button icon='pi pi-angle-left' class='p-button-rounded p-button-outlined' title='Up'
        :disabled='path.length == 0' @click='goUp' />
    </div>
    <div id='path-wrapper' class='block'>
      <div id='path' class='block'>
        <div class='item' @click='goToRoot'>
          <span class='pi pi-home' />
        </div>
        <div v-for='(item_name, index) in path' :key='item_name.id' class='block'>
          <span class='pi pi-chevron-right separator' />
          <div class='item' @click='goTo(index)'>
            {{ item_name }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'v-breadcrumb',
  props: {
    path: {
      type: Array,
      default: new Array()
    }
  },
  setup(props, { emit }) {
    function goUp() {
      if (props.path.length != 0) {
        emit('goTo', props.path.slice(0, props.path.length - 1))
      }
    }

    function goToRoot() {
      if (props.path.length != 0) {
        emit('goTo', [])
      }
    }

    function goTo(index) {
      if (index != props.path.length - 1) {
        emit('goTo', props.path.slice(0, index + 1))
      }
    }

    return {
      goUp, goToRoot, goTo
    }
  }
}
</script>

<style scoped>
#breadcrumb {
  display: flex;
  flex: 1;
}

.block {
  display: flex;
  align-items: center;
}

#path-wrapper {
  position: relative;
  flex: 1;
  font-size: 1.2rem;
}

#path {
  position: absolute;
  width: 100%;
  overflow-y: auto;
}

.item {
  cursor: pointer;
  margin: 0em 0.1em;
  padding: 0em 0.1em;
}

.item:hover {
  background-color: whitesmoke;
  border-radius: 5px;
}

.separator {
  font-size: 0.6rem;
}
</style>