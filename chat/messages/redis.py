from django.conf import settings
from redis import StrictRedis


def get_connection():
    return StrictRedis.from_url(settings.MESSAGE_BROKER, decode_responses=True)


def add_message(content, conversation_uuid, author, date):
    r = get_connection()
    payload = {"content": content, "author": author.value, "date": date.isoformat()}
    msg_id = r.xadd(conversation_uuid.hex, payload)
    r.expire(conversation_uuid.hex, settings.CONVERSATION_EXPIRATION)
    return payload.update({"id": msg_id})


def get_messages(conversation_uuid, since=0):
    r = get_connection()
    messages = r.xrange(conversation_uuid, since, "+")
    result = []

    for msg_id, message in messages:
        message["id"] = msg_id
        result.append(message)

    return result
