from datetime import datetime
import uuid
from typing import List, Optional
from ninja import Schema, ModelSchema
from ninja.pagination import RouterPaginated
from .models import Conversation, Message

router = RouterPaginated()


class MessageOut(ModelSchema):

    class Meta:
        model = Message
        fields = ["id", "date", "content", "author"]

    conversation: uuid.UUID

    @staticmethod
    def resolve_conversation(obj):
        return obj.conversation.uuid


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


@router.post("/", response=List[MessageOut])
def create_message_and_list(request, data: MessageIn, since: int = None):
    conv = None

    # retrieve requested conversation
    if data.conversation:
        conv = Conversation.objects.filter(uuid=data.conversation).first()

    # create new conversation if not found or if first message (no uuid provided)
    if not conv:
        user = None
        if request.user.is_authenticated:
            user = request.user
        conv = Conversation.objects.create(
            customer_name=data.name, customer_email=data.email, customer=user
        )

    author = Message.AuthorChoice.CUSTOMER

    if (
        request.user.is_authenticated
        and request.user.groups.filter(name="agent").exists()
    ):
        author = Message.AuthorChoice.AGENT

    Message.objects.create(
        conversation=conv,
        author=author,
        content=data.content,
    )

    return list_messages(request, conv.uuid, since=since)
