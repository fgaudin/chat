import uuid
from typing import Optional
from ninja import Schema
from ninja.pagination import RouterPaginated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import create_message

router = RouterPaginated()


class MessageIn(Schema):
    conversation: Optional[uuid.UUID] = None
    name: Optional[str] = None
    email: Optional[str] = None
    content: str


class ConversationOut(Schema):
    conversation: uuid.UUID


@router.post("/", response={201: ConversationOut})
def create_message_and_list(request, data: MessageIn):
    result = create_message(
        data.content,
        conversation_uuid=data.conversation,
        name=data.name,
        email=data.email,
        user=request.user,
    )

    channel_layer = get_channel_layer()
    group_name = result["conversation"].uuid.hex
    async_to_sync(channel_layer.group_send)(group_name, {"type": "message.received"})

    return 201, {"conversation": result["conversation"].uuid}
