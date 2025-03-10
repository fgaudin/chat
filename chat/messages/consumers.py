import json
from os import sync

from asgiref.sync import async_to_sync, sync_to_async
from channels.db import database_sync_to_async

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .api_messages import MessageOut
from .models import Message


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
        messages = Message.objects.filter(conversation__uuid=self.conv_clean)

        return list(messages.filter(id__gt=self.since).order_by("id"))

    async def send_latest_messages(self):
        messages = await self.latest_messages()
        payload = {
            "items": [
                MessageOut.from_orm(message).model_dump(mode="json")
                for message in messages
            ]
        }

        self.since = messages[-1].id if messages else self.since

        await self.send_json(payload)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.conv_clean, self.channel_name)

    async def message_received(self, event):
        await self.send_latest_messages()
