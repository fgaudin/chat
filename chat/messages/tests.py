import email
from unittest.mock import ANY
import uuid
from django.test import TestCase
from ninja.testing import TestClient
from .models import Conversation, Message
from messages.api_messages import router as message_router
from messages.api_conversations import router as conversation_router
from django.contrib.auth.models import User, Group


class MessageApiTest(TestCase):
    def setUp(self):
        self.maxDiff = None

        self.client = TestClient(message_router)

        self.agent_group, _ = Group.objects.get_or_create(name="agent")

    def test_get_messages_no_uuid(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 405)

    def test_get_messages_wrong_uuid(self):
        response = self.client.get(f"/{str(uuid.uuid4())}/")

        self.assertEqual(response.status_code, 200)
        expected = {"items": [], "count": 0}
        self.assertEqual(response.json(), expected)

    def test_get_messages(self):
        conversation = Conversation.objects.create()
        message1 = conversation.messages.create(
            content="Hello", author=Message.AuthorChoice.CUSTOMER
        )
        message2 = conversation.messages.create(
            content="Hi", author=Message.AuthorChoice.AGENT
        )

        response = self.client.get(f"/{conversation.uuid.hex}/")

        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(result["count"], 2)

        expected = [
            {
                "author": "CUS",
                "content": "Hello",
                "conversation": str(conversation.uuid),
                "date": ANY,
                "id": message1.id,
            },
            {
                "author": "AGE",
                "content": "Hi",
                "conversation": str(conversation.uuid),
                "date": ANY,
                "id": message2.id,
            },
        ]
        self.assertEqual(result["items"], expected)

        response = self.client.get(f"/{conversation.uuid.hex}/?since={message1.id}")

        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"], expected[1:])

    def test_create_first_message_as_anonymous(self):
        response = self.client.post("/", json={"content": "Hello"})

        self.assertEqual(response.status_code, 200, response.json())

        result = response.json()
        result = response.json()
        self.assertEqual(result["count"], 1)
        expected = [
            {
                "author": "CUS",
                "content": "Hello",
                "conversation": ANY,
                "date": ANY,
                "id": ANY,
            }
        ]
        self.assertEqual(result["items"], expected)

        conversation = Conversation.objects.first()
        self.assertEqual(conversation.customer_name, None)
        self.assertEqual(conversation.customer_email, None)
        self.assertEqual(conversation.customer, None)
        self.assertEqual(conversation.assignee, None)
        self.assertEqual(conversation.status, "OPEN")

    def test_create_first_message_with_name_and_email(self):
        response = self.client.post(
            "/",
            json={"name": "Alice", "email": "alice@test.com", "content": "Hello"},
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["count"], 1)
        expected = [
            {
                "author": "CUS",
                "content": "Hello",
                "conversation": ANY,
                "date": ANY,
                "id": ANY,
            }
        ]
        self.assertEqual(result["items"], expected)

        conversation = Conversation.objects.first()
        self.assertEqual(conversation.customer_name, "Alice")
        self.assertEqual(conversation.customer_email, "alice@test.com")
        self.assertEqual(conversation.customer, None)

    def test_create_first_message_as_authenticated(self):
        user = User.objects.create_user("Bob", email="bob@test.com")
        response = self.client.post("/", json={"content": "Hi"}, user=user)

        self.assertEqual(response.status_code, 200)
        result = response.json()
        expected = [
            {
                "author": "CUS",
                "content": "Hi",
                "conversation": ANY,
                "date": ANY,
                "id": ANY,
            }
        ]
        self.assertEqual(result["items"], expected)

        conversation = Conversation.objects.first()
        self.assertEqual(conversation.customer_name, None)
        self.assertEqual(conversation.customer_email, None)
        self.assertEqual(conversation.customer, user)

    def test_create_add_message(self):
        conversation1 = Conversation.objects.create()
        conversation1.messages.create(
            content="Hello1", author=Message.AuthorChoice.CUSTOMER
        )
        conversation2 = Conversation.objects.create()
        message2 = conversation2.messages.create(
            content="Hello2", author=Message.AuthorChoice.CUSTOMER
        )
        conversation3 = Conversation.objects.create()
        conversation3.messages.create(
            content="Hello3", author=Message.AuthorChoice.CUSTOMER
        )

        user = User.objects.create_user("Agent", email="agent@test.com")
        user.groups.add(self.agent_group)

        response = self.client.post(
            f"/?since={message2.id}",  # can't find how to pass query params properly
            json={
                "conversation": conversation2.uuid.hex,
                "content": "How can I help you",
            },
            user=user,
        )

        self.assertEqual(response.status_code, 200, response.json())

        result = response.json()
        expected = [
            {
                "author": "AGE",
                "content": "How can I help you",
                "conversation": str(conversation2.uuid),
                "date": ANY,
                "id": ANY,
            }
        ]
        self.assertEqual(result["items"], expected)


class ConversationApiTest(TestCase):
    def setUp(self):
        self.maxDiff = None

        self.client = TestClient(conversation_router)

        self.agent_group, _ = Group.objects.get_or_create(name="agent")
        self.user = User.objects.create_user("Agent", email="agent@test.com")
        self.user.groups.add(self.agent_group)

        self.user2 = User.objects.create_user("Agent2", email="agent2@test.com")
        self.user2.groups.add(self.agent_group)

        self.customer = User.objects.create_user("Alice", email="alice@test.com")

        self.conv1 = Conversation.objects.create()
        self.conv2 = Conversation.objects.create(assignee=self.user)
        self.conv3 = Conversation.objects.create(
            status=Conversation.ConversationStatus.CLOSED, assignee=self.user2
        )

    def test_list_conversations_unauthenticated(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 401, response.json())

    def test_list_conversations(self):
        response = self.client.get("/", user=self.user)

        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(result["count"], 3)
        expected = {
            "id": self.conv2.id,
            "uuid": str(self.conv2.uuid),
            "created_at": ANY,
            "customer_name": None,
            "customer_email": None,
            "status": "OPEN",
            "assignee": self.user.id,
        }

        self.assertEqual(result["items"][1], expected)

    def test_list_conversations_not_agent(self):
        response = self.client.get("/", user=self.customer)

        self.assertEqual(response.status_code, 401)

        result = response.json()
        self.assertEqual(result["detail"], "Unauthorized")

    def test_list_conversations_assigned(self):
        response = self.client.get("/?assigned=true", user=self.user)

        result = response.json()
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["items"][0]["id"], self.conv2.id)
        self.assertEqual(result["items"][1]["id"], self.conv3.id)

    def test_list_open_conversations(self):
        response = self.client.get("/?status=OPEN", user=self.user)

        result = response.json()
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["items"][0]["id"], self.conv1.id)
        self.assertEqual(result["items"][1]["id"], self.conv2.id)

    def test_list_closed_conversations(self):
        response = self.client.get("/?status=CLOSED", user=self.user)

        result = response.json()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["id"], self.conv3.id)

    def test_list_conversations_assigned_to_me(self):
        response = self.client.get("/?assigned_to_me=true", user=self.user)

        result = response.json()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["id"], self.conv2.id)

    def test_close_conversation(self):
        response = self.client.patch(f"/{self.conv1.id}/close", user=self.user)

        self.assertEqual(response.status_code, 200)

        conv = Conversation.objects.get(id=self.conv1.id)
        self.assertEqual(conv.status, Conversation.ConversationStatus.CLOSED)

    def test_open_conversation(self):
        response = self.client.patch(f"/{self.conv3.id}/open", user=self.user)

        self.assertEqual(response.status_code, 200)

        conv = Conversation.objects.get(id=self.conv3.id)
        self.assertEqual(conv.status, Conversation.ConversationStatus.OPEN)

    def test_take_conversation(self):
        response = self.client.patch(f"/{self.conv1.id}/take", user=self.user)

        self.assertEqual(response.status_code, 200)

        conv = Conversation.objects.get(id=self.conv1.id)
        self.assertEqual(conv.assignee, self.user)
