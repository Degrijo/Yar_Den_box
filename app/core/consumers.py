from json import loads, dumps
from random import sample, shuffle

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
# from channels.db import database_sync_to_async
from rest_framework_simplejwt import authentication
from rest_framework_simplejwt.tokens import AccessToken

from app.core.models import Room, UserTaskRoom, Task, Player
from django.contrib.auth import get_user_model


class RoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + self.room_name
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()
        self.send(text_data=dumps({'message': 'connection ok'}))

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {'type': 'input_room'})
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def group_message(self, event):
        self.send(event.get('data'))

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        data = loads(text_data)
        event_type = data.get('eventType')
        room = Room.objects.get(name=self.room_name)
        token = authentication.JWTAuthentication().get_validated_token(data.get('token'))
        user = authentication.JWTAuthentication().get_user(token)
        if event_type == 'greeting':
            player, _ = Player.objects.get_or_create(user=user, room=room)
            players = Player.objects.filter(room__name=self.room_name).values('id', 'user__username')
            self.send(dumps({'isHost': player.host}))
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                'type': 'group_message',
                'data': dumps({'users': list(players)})
            })
        elif event_type == 'start':
            room.status = Room.WORKING
            room.save()
            user_count = room.players.count()
            if user_count < 2:
                self.send(dumps({'event_type': 'error', 'message': 'Count of users smaller than 2'}))
                return
            tasks = Task.objects.exclude(rooms_id=room.id)
            if tasks.count() < user_count:
                self.send({'event_type': 'error',
                           'message': 'Task counter should be bigger or equal than user counter'})
                return
            room.status = Room.WORKING
            room.save()
            game_tasks = sample(list(tasks.values_list('id', flat=True)), k=user_count)
            repetitive_tasks = game_tasks.copy()
            repetitive_tasks.append(repetitive_tasks.pop(0))
            users = list(room.users.values_list('id', flat=True))
            shuffle(users)
            scope_cost = room.current_round * (user_count - 2) * 10
            for i in range(user_count):
                UserTaskRoom.objects.create(task_id=game_tasks[i], player_id=users[i], scope_cost=scope_cost)
                UserTaskRoom.objects.create(task_id=repetitive_tasks[i], user_id=users[i], scope_cost=scope_cost)
            self.send(dumps(UserTaskRoom.objects.values('player__user__username', 'player__id', 'task__title')))
        elif event_type == 'answer':
            room = Room.objects.get(name=self.room_name)

            data.get('answer')
        elif event_type == 'vote':
            pass
        elif event_type == 'finish':
            pass
        # user = authentication.JWTAuthentication().get_user(text_data.get('token'))
        # print(user.username)
