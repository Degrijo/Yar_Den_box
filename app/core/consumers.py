from json import loads, dumps

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
# from channels.db import database_sync_to_async
from rest_framework_simplejwt import authentication

from app.core.models import Room, UserTaskRoom
from django.contrib.auth import get_user_model


class RoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + self.room_name
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()
        room = Room.objects.get(name=self.room_name)
        self.send(text_data=dumps({'users': list(room.users.values('id', 'username'))}))

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {'type': 'input_room'})
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        data = loads(text_data)
        event_type = data.get('event_type')
        if event_type == 'start':
            room = Room.objects.get(name=self.room_name)
            room.status = Room.WORKING
            room.save()
        if event_type == 'answer':
            pass
        if event_type == 'vote':
            pass
        if event_type == 'finish':
            pass
        # user = authentication.JWTAuthentication().get_user(text_data.get('token'))
        # print(user.username)
