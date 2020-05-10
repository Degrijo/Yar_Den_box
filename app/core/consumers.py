from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async

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
        username = text_data_json.get('username')
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
            'type': 'input_room',
            'username': username
        })

    def chat_message(self, event):
        username = event.get('username')
        self.send(text_data=json.dumps({
            'event': 'Send',
            'username': username
        }))



