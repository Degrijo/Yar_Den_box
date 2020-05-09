from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

import json


class RoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_' + self.room_name
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.room_name)
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.room_name)

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        message = json.loads(text_data)['message']
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
            'type': 'chat_message',
            'message': message
        })

    def chat_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'event': 'Send', 'message': message
        }))
