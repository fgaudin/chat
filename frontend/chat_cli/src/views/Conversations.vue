<script setup lang="ts">
import Chat from '@/components/Chat.vue'
import axios from 'axios'
import { onMounted, ref } from 'vue'

const props = defineProps<{
  conversation?: string
}>()

type Conversation = {
  id: number
  uuid: string
  created_at: string
  customer_name: string
  customer_email: string
  status: string
  assignee: null
}

const conversations = ref<Conversation[]>([])

onMounted(async () => {
  try {
    const response = await axios.get('/api/conversation/')
    conversations.value = response.data.items
  } catch (error) {
    console.error(error)
  }
})
</script>

<template>
  <main>
    <div id="conversation-list">
      <ul>
        <li class="conv" v-for="conversation in conversations" :key="conversation.id">
          <router-link :to="'/conversation/' + conversation.uuid">
            {{ conversation.created_at }} - {{ conversation.status }}
          </router-link>
        </li>
      </ul>
    </div>
    <div id="chat">
      <Chat
        v-if="props.conversation"
        side="agent"
        :conversation="props.conversation"
        :key="props.conversation"
      />
    </div>
  </main>
</template>

<style scoped>
main {
  padding: 1rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
}

#conversation-list {
  border-right: 1px solid #ccc;
  padding-right: 1rem;
}

.conv {
  /* make it pretty */

  list-style: none;
  padding: 1rem;
  border: 1px solid #ccc;
  cursor: pointer;
}

#chat {
  padding-left: 1rem;
}
</style>
