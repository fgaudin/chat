from ninja import NinjaAPI

api = NinjaAPI()

api.add_router("/messages", "messages.api_messages.router")
api.add_router("/conversation", "messages.api_conversations.router")
