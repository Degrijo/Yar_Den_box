from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter

from app.core.consumers import RoomConsumer

application = ProtocolTypeRouter({
    "websocket":
        URLRouter([
            re_path(r'game/(?P<room_name>\w+)/$', RoomConsumer),
        ])
})
