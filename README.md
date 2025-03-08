# chat example

Simple Django app defining models and API for a Customer Chat

## Installing

Uses `uv` package manager:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

To install packages, run in this directory:

```
uv sync
```

To create the default SQLite DB:

```
source .venv/bin/activate
cd chat
./manage.py migrate
```

## Run tests

```
./manage.py test
```

## API documentation

```
./manage.py runserver
```

and visit: http://localhost:8000/api/docs

## Code organization

The app uses Django with Django Ninja for the API layer.

The data model is in `chat/messages/models.py`.

The chat API is in `chat/messages/api_messages.py`.

The `chat/messages/api_conversations.py` APIs are some CRUD operations for the agent side.

Tests are in `chat/messages/tests.py`.

## Description of API

When the customer posts their first message, the frontend would first call `POST /api/messages/`, which takes the following payload:

```
{
  "conversation": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  # optional
  "name": "string",  # optional
  "email": "string",  # optional
  "content": "string"
}
```

The first message contains no conversation uuid.
It can contain a name and/or email.
Only content is required.
If the user is logged in, it will be associated to the conversation.

This will create a message associated to the passed conversation or to a new one if missing/invalid.

The response has this format:

```
{
  "items": [
    {
      "conversation": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "id": 1,
      "date": "2025-03-08T17:21:49.677Z",
      "content": "Hello",
      "author": "CUS"
    }
  ],
  "count": 1
}
```

The frontend should store the conversation uuid for future polling.
`author` can be `CUS` for customer or `AGE` for agent.

To get answers from the agent, the frontent should do a regular polling with `GET /api/messages/{uuid}/?since=1` where `uuid` is the conversation and `since=1` is the last message id received.
The answer is the list of new messages with the same format.

On the agent side, the list of conversations is available through `GET /api/conversation/` and the frontend can then start polling messages in the same way through `GET /api/messages/{uuid}`, omitting the `since` parameter initially.

Following messages sent by either side should include the `since` parameter `POST /api/messages/?since=x` in their requests to only get the new messages in response.

The frontend should make sure that no messages are duplicated.

## Possible improvements

- use a MySQL or PostgreSQL for data.
- use Redis Streams for message storage and have a replication process to replicate them if needed for long term storage/analysis.
- use websockets to avoid polling.
