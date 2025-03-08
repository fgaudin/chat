import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Conversation(models.Model):

    class ConversationStatus(models.TextChoices):
        OPEN = "OPEN", _("Open")
        CLOSED = "CLOSED", _("Closed")

    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    # if customer is logged in, we can associate it with the conversation, but we also allow anonymous customers
    customer = models.ForeignKey(
        "auth.User", on_delete=models.DO_NOTHING, null=True, blank=True
    )
    # if customer is not logged in, we can store the email
    customer_email = models.EmailField(null=True, blank=True)
    customer_name = models.CharField(max_length=255, null=True, blank=True)

    assignee = models.ForeignKey(
        "auth.User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="assigned_conversations",
    )

    status = models.CharField(
        max_length=255,
        choices=ConversationStatus.choices,
        default=ConversationStatus.OPEN,
    )

    def __str__(self):
        if self.customer:
            customer = self.customer.email
        else:
            customer = self.customer_email or self.customer_name
        return f"{self.uuid} - {customer} - assigned to: {self.assignee or '-'}"


class Message(models.Model):
    class AuthorChoice(models.TextChoices):
        CUSTOMER = "CUS", _("Customer")
        AGENT = "AGE", _("Agent")

    conversation = models.ForeignKey(
        Conversation, on_delete=models.DO_NOTHING, related_name="messages"
    )
    date = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=3, choices=AuthorChoice.choices)
    content = models.TextField()
