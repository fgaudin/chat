import email
from unittest.mock import ANY
import uuid
from django.test import TestCase
from ninja.testing import TestClient
from .models import Conversation, Message
from messages.api import router
from django.contrib.auth.models import User, Group


class MessageApiTest(TestCase):
    def setUp(self):
        self.maxDiff = None

        self.client = TestClient(router)

        self.agent_group = Group.objects.create(name="agent")

    def test_get_messages_no_uuid(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 405)

    def test_get_messages_wrong_uuid(self):
        response = self.client.get(f"/{uuid.uuid4()}/")

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
            "/", json={"name": "Alice", "email": "alice@test.com", "content": "Hello"}
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
