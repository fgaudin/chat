<script setup lang="ts">
import axios from 'axios'
import { onMounted, onUnmounted, onUpdated, reactive, ref, useTemplateRef, watch } from 'vue'
import { onBeforeRouteUpdate, useRoute } from 'vue-router'

const props = defineProps<{
  side: string // customer or agent
  conversation?: string
}>()

const message = ref('')
const sending = ref(false)
const messages = reactive(new Map<number, Message>())
const since = ref(0)
const bottom = useTemplateRef('bottom')
let currentConv: string
let pollHandler: any
const delay = 1000
let scroll = false

interface Message {
  id: number
  content: string
  date: string
  author: string
  conversation: string
}

onMounted(() => {
  console.log('watched')
  if (props.side === 'agent') {
    currentConv = props.conversation || ''
  } else {
    currentConv = sessionStorage.getItem('conv') || ''
  }
  console.log(currentConv)
  pollMessages()
})

onUnmounted(() => {
  if (pollHandler) clearTimeout(pollHandler)
})

onUpdated(() => {
  if (scroll) {
    scrollToBottom()
  }
})

const sendMessage = async () => {
  console.log('Message sent: ', message.value)

  sending.value = true
  let startPolling = false

  const payload: any = {
    content: message.value,
  }
  if (currentConv) {
    payload.conversation = currentConv
  } else {
    startPolling = true
  }

  try {
    const response = await axios.post(`/api/messages/?since=${since.value}`, payload)
    if (response.status !== 200) {
      throw new Error('Failed to send message')
    }
    const messages = response.data.items

    if (props.side === 'customer') {
      currentConv = messages[0].conversation
      console.log('Conversation ID: ', currentConv)
      sessionStorage.setItem('conv', currentConv)
    }
    addMessages(messages)
    if (startPolling) {
      pollMessages()
    }
  } catch (error) {
    console.error(error)
  } finally {
    sending.value = false
  }

  message.value = ''
}

const addMessages = (newMessages: Message[]) => {
  newMessages.forEach((msg) => {
    if (!messages.has(msg.id)) {
      messages.set(msg.id, msg)
      if (msg.id > since.value) {
        since.value = msg.id
      }
    }
  })
  if (newMessages.length > 0) {
    scroll = true
  }
}

const pollMessages = async () => {
  if (!currentConv) {
    return
  }

  try {
    const response = await axios.get(`/api/messages/${currentConv}/?since=${since.value}`)
    if (response.status !== 200) {
      throw new Error('Failed to fetch messages')
    }
    addMessages(response.data.items)
    pollHandler = setTimeout(pollMessages, delay)
  } catch (error) {
    console.error(error)
  }
}

const scrollToBottom = () => {
  bottom.value?.scrollIntoView({ behavior: 'smooth' })
}

const name = (message: Message) => {
  if (message.author === 'CUS') {
    if (props.side === 'customer') {
      return 'Me'
    } else {
      return 'Customer'
    }
  } else {
    if (props.side === 'customer') {
      return 'Agent'
    } else {
      return 'Me'
    }
  }
}
</script>

<template>
  <div id="messages">
    <p v-for="[id, msg] in messages" :key="msg.id">
      <span class="author">{{ name(msg) }}: </span>{{ msg.content }}
    </p>
    <div ref="bottom" id="bottom"></div>
  </div>
  <form @submit.prevent="sendMessage">
    <input type="text" v-model="message" placeholder="Type your message here" />
    <input type="submit" value="Send" />
  </form>
</template>

<style scoped>
#messages {
  height: 10rem;
  overflow-y: scroll;
  margin-top: 1rem;
}

.author {
  font-style: italic;
  color: grey;
}

#bottom {
  height: 1px;
}
</style>
