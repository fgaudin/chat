from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/messages/(?P<conversation>[0-9a-f-]+)/$",
        consumers.MessageConsumer.as_asgi(),
    ),
]
