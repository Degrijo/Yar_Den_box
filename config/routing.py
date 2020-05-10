from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from app.core.middlewares import MyMiddleware

from app.core.consumers import RoomConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r'game/(?P<room_name>\w+)/$', RoomConsumer),
        ])
    )
})
