from datetime import datetime
import uuid
from typing import List, Optional
from ninja import Schema, ModelSchema
from ninja.pagination import RouterPaginated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Conversation, Message

router = RouterPaginated()


class MessageOut(ModelSchema):

    class Meta:
        model = Message
        fields = ["id", "date", "content", "author"]


@router.get("/{conversation}/", response=List[MessageOut])
def list_messages(
    request,
    conversation: uuid.UUID,
    since: int = None,
):
    messages = Message.objects.filter(conversation__uuid=conversation).select_related(
        "conversation"
    )

    if since:
        messages = messages.filter(id__gt=since)

    return messages.order_by("id")


class MessageIn(Schema):
    conversation: Optional[uuid.UUID] = None
    name: Optional[str] = None
    email: Optional[str] = None
    content: str


class ConversationOut(Schema):
    conversation: uuid.UUID


@router.post("/", response={201: ConversationOut})
def create_message_and_list(request, data: MessageIn):
    message = Message.objects.create_message(
        data.content,
        conversation_uuid=data.conversation,
        name=data.name,
        email=data.email,
        user=request.user,
    )

    channel_layer = get_channel_layer()
    group_name = message.conversation.uuid.hex
    async_to_sync(channel_layer.group_send)(group_name, {"type": "message.received"})

    return 201, {"conversation": message.conversation.uuid}
