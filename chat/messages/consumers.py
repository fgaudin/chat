from channels.db import database_sync_to_async

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .redis import get_messages


class MessageConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.since = 0

    async def connect(self):
        self.conversation = self.scope["url_route"]["kwargs"]["conversation"]
        self.conv_clean = self.conversation.replace("-", "")

        await self.channel_layer.group_add(self.conv_clean, self.channel_name)

        await self.accept()

        await self.send_latest_messages()

    @database_sync_to_async
    def latest_messages(self):
        messages = get_messages(self.conv_clean, since=self.since)

        return messages

    async def send_latest_messages(self):
        messages = await self.latest_messages()

        payload = {"items": messages}

        self.since = messages[-1]["id"] if messages else self.since

        await self.send_json(payload)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.conv_clean, self.channel_name)

    async def message_received(self, event):
        await self.send_latest_messages()
