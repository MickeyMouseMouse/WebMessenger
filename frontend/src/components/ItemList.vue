<template>
  <div class='item-list'>
    <div v-for='item in list' :key='item.id'
      v-show='getVisible(item)'
      :class="['item', active_item_id == item.id ? 'selected' : 'unselected']"
      @click="$emit('select', item)">
      <div style='display: flex; flex: 1'>
        <div :class='getPicture(item)' />
        <div style='margin-left: 0.5em'>
          {{ item.name }}
        </div>
        <div v-show='item.online' title='Online' style='display: flex; align-items: center; margin-left: 0.5em'>
          <div style='width: 0.5em; height: 0.5em; border-radius: 90px; background-color: green' />
        </div>
        <div v-if='show_ownership && item.is_owner' style='display: flex; align-items: center; margin-left: 0.5em; color: grey'>
          owner
        </div>
      </div>
      <div v-show='item.unread_counter' class='unread-counter'>
        <div style='margin-right: 0.2em'>
          {{ item.unread_counter }}
        </div>
        <div class='pi pi-envelope' />
      </div>
      <div style='margin-left: 0.5em'>
        <Button v-if='remove_btn' icon='pi pi-trash' severity='danger' :disabled='item.is_owner' @click="$emit('remove', item)" />
        <Button v-if='add_btn' icon='pi pi-user-plus' @click="$emit('add', item)" />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'v-item-list',
  props: {
    list: Array,
    active_item_id: Number,
    show_ownership: Boolean,
    add_btn: Boolean,
    remove_btn: Boolean,
    filter: String,
  },
  setup(props) {
    const getVisible = (item) => !props.filter || item.name.toLowerCase().indexOf(props.filter.toLowerCase()) != -1

    function getPicture(item) {
      if (item.type == 'group') return 'pi pi-users'
      if (item.type == 'channel') return 'pi pi-megaphone'
      return 'pi pi-user'
    }

    return {
      getVisible, getPicture
    }
  }
}
</script>

<style scoped>
.item-list {
  cursor: pointer;
}

.item {
  display: flex;
  align-items: center;
  height: 3.5em;
  padding: 0em 0.5em; 
  border-bottom: 1px solid lightgray;
}

.unselected:hover {
  background-color: #f5f6f8;
  transition: 100ms;
}

.selected {
  color: white;
  background-color: #419fd9;
}

.unread-counter {
  display: flex;
  align-items: center;
  padding-right: 1em;
}
</style>
