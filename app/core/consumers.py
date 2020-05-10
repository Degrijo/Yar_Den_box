from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async

from rest_framework_simplejwt import authentication

import json

from app.core.models import Room


class RoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + self.room_name
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.room_name)
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.room_name)

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        text_data_json = json.loads(text_data)
        token = text_data_json.get('token')
        user = authentication.JWTAuthentication().get_user(token)
        room = user.room
        async_to_sync(self.channel_layer.group_send)(self.room_group_name)

    def chat_message(self, event):
        data = self.connect()
        self.send(text_data=json.dumps(data))

    async def connect(self):
        return await database_sync_to_async(self.get_inf)()

    def get_inf(self):
        room = Room.objects.get(name=self.room_name)
        return {
            "room": room.name,
             "users": list(room.users.values('id', "username", "score")),
             "tasks": list(room.userroomtasks.values("task_id", "user_id", "status", "likes"))
        }
