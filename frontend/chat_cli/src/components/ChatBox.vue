<script setup lang="ts">
import { ref } from 'vue'
import Chat from './Chat.vue'

const chatVisible = ref(false)

const showChat = () => {
  chatVisible.value = !chatVisible.value
}
</script>

<template>
  <div id="chat-box">
    <h2 @click="showChat" id="chat-header">Contact us!</h2>
    <div id="chat-content" v-if="chatVisible">
      <Chat side="customer" />
    </div>
  </div>
</template>

<style scoped>
#chat-box {
  position: fixed;
  bottom: 0;
  right: 2rem;
  width: 20rem;
  background-color: #333;
  color: white;
  padding: 1rem;
  border-top-left-radius: 0.5rem;
  border-top-right-radius: 0.5rem;
}

#chat-header {
  cursor: pointer;
}
</style>
