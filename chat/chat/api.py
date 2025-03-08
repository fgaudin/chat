from ninja import NinjaAPI

api = NinjaAPI()

api.add_router("/messages/", "messages.api.router")
