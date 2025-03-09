from datetime import datetime
from typing import List, Optional
from django.shortcuts import get_object_or_404
from ninja import Schema, ModelSchema
from ninja.pagination import RouterPaginated
from .models import Conversation
from ninja.security import django_auth

router = RouterPaginated()


class ConversationOut(ModelSchema):

    class Meta:
        model = Conversation
        fields = [
            "id",
            "uuid",
            "created_at",
            "customer_name",
            "customer_email",
            "status",
            "assignee",
        ]


def agent_auth(request):
    if (
        request.user.is_authenticated
        and request.user.groups.filter(name="agent").exists()
    ):
        return request.user
    return None


@router.get("/", response=List[ConversationOut], auth=agent_auth)
def list_conversations(
    request, assigned: str = None, status: str = None, assigned_to_me: bool = None
):
    conversations = Conversation.objects.all()
    if assigned == "true":
        conversations = conversations.filter(assignee__isnull=False)
    elif assigned == "false":
        conversations = conversations.filter(assignee__isnull=True)

    if assigned_to_me:
        conversations = conversations.filter(assignee=request.user)

    if status:
        conversations = conversations.filter(status=status)

    return conversations.order_by("-created_at", "-status")


@router.patch("/{id}/close", response=ConversationOut, auth=agent_auth)
def close_conversation(request, id: int):
    conversation = get_object_or_404(Conversation, pk=id)
    conversation.status = Conversation.ConversationStatus.CLOSED
    conversation.save()

    return conversation


@router.patch("/{id}/open", response=ConversationOut, auth=agent_auth)
def open_conversation(request, id: int):
    conversation = get_object_or_404(Conversation, pk=id)
    conversation.status = Conversation.ConversationStatus.OPEN
    conversation.save()

    return conversation


@router.patch("/{id}/take", response=ConversationOut, auth=django_auth)
def take_conversation(request, id: int):
    conversation = get_object_or_404(Conversation, pk=id)
    conversation.assignee = request.user
    conversation.save()

    return conversation
