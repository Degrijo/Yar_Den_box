from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
# from channels.db import database_sync_to_async
#
# from rest_framework_simplejwt import authentication

import json

from app.core.models import Room, UserTaskRoom
from django.contrib.auth import get_user_model


class RoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + self.room_name
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        # text_data_json = json.loads(text_data)
        # token = text_data_json.get('token')
        # user = authentication.JWTAuthentication().get_user(token)
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
            'type': 'input_room',
            'message': ''
        })

    def input_room(self, event):
        room = Room.objects.get(name=self.room_name)
        data = {
            "room": room.name,
            "users": list(room.users.values('id', "username", "score", "role")),
            "tasks": list(room.userroomtasks.tasks.values('id', 'title')),
            "usertasks": list(room.userroomtasks.values("task_id", "user_id", "status", "likes", 'scope_cost')),
        }
        types = dict(get_user_model().ROLE_TYPES)
        for user in data['users']:
            user['role'] = types.get(user['role'])
        types = dict(UserTaskRoom.STATUS_TYPES)
        for usertask in data['usertasks']:
            usertask['status'] = types.get(usertask['status'])
        self.send(text_data=json.dumps(data))
