<template>
  <div id='calls-page'>
    <video id='video' />
    <div id='bottom'>
      <Button icon='pi pi-camera' outlined rounded />
      <Button icon='pi pi-phone' severity='success' rounded style='margin-right: 2em' />
      <Button icon='pi pi-phone' severity='danger' rounded style='rotate: 135deg' />
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
export default {
  name: 'v-calls-page',
  mounted() {
    //this.init()
  },
  methods: {
    async init() {
      let stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: true
      })

      document.getElementById('video').srcObject = stream
      window.stream = stream
    },
    ...mapActions([
      
    ])
  },
  computed: {
    ...mapGetters([
      
    ])
  }
}
</script>

<style scoped>
#calls-page {
  flex: 1;
  position: relative;
}

#video {
  width: 100%;
  height: 100%;
}

#bottom {
  display: flex;
  justify-content: center;
  padding-bottom: 3em;
  position: absolute;
  bottom: 0;
  width: 100%;
}
</style>