import json
from random import sample, shuffle

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db.models import F, Count, Q
from rest_framework_simplejwt import authentication

from app.core.models import Room, UserTaskRoom, Task, Player
from app.core.utils import vote_event, greeting_event, error_event, start_event, is_alive_event, define_event, \
    answer_accepted_event, connection_event, winner_event


QUESTION_NUMBER_IN_ROUND = 2
MIN_PLAYER_NUMBER = 2
SCOPE_ORDER = 10


class RoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + self.room_name
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()
        self.send(connection_event())

    def disconnect(self, code):
        # check, if group steal has connections
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def group_message(self, event):
        self.send(event.get('data'))

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        try:
            data = json.loads(text_data)
            print(data)
            event_type = data.get('eventType')
            room = Room.objects.get(name=self.room_name)  # store in object
            token = authentication.JWTAuthentication().get_validated_token(data.get('token'))
            user = authentication.JWTAuthentication().get_user(token)  # store in object
            player = Player.objects.get(user=user, room=room)  # store in object
            if event_type == 'greeting':
                players = Player.objects.filter(room__name=self.room_name).values('id', username=F('user__username'))
                self.send(define_event(player.id, user.username, player.host))
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'group_message',
                    'data': greeting_event(list(players))
                })
            elif event_type == 'start':
                player_count = room.players.count()
                if player_count < MIN_PLAYER_NUMBER:
                    self.send(error_event('Amount of users smaller than ' + MIN_PLAYER_NUMBER))
                    return
                all_tasks = Task.objects.exclude(rooms__id=room.id)  # all()
                if all_tasks.count() < player_count:
                    self.send({'event_type': 'error',
                               'message': 'Task counter should be bigger or equal than user counter'})
                    return
                room.status = Room.WORKING
                room.save(update_fields=('status',))
                if room.players.annotate(task_count=Count('userroomtasks',
                                                          filter=Q(userroomtasks__status=UserTaskRoom.PENDING)))\
                               .filter(task_count__lt=QUESTION_NUMBER_IN_ROUND):  # check with completed usertaskrooms
                    game_tasks = sample(list(all_tasks.values_list('id', flat=True)), k=player_count)
                    repetitive_tasks = game_tasks.copy()
                    repetitive_tasks.append(repetitive_tasks.pop(0))
                    players = list(room.players.values_list('id', flat=True))
                    shuffle(players)
                    scope_cost = room.current_round * (player_count - 1) * SCOPE_ORDER
                    for i in range(player_count):
                        UserTaskRoom.objects.create(task_id=game_tasks[i],
                                                    player_id=players[i],
                                                    room=room,
                                                    scope_cost=scope_cost)
                        UserTaskRoom.objects.create(task_id=repetitive_tasks[i],
                                                    player_id=players[i],
                                                    room=room,
                                                    scope_cost=scope_cost)
                tasks = []
                for player in room.players.all():  # update with sql
                    tasks.append({'userId': player.id,
                                  'username': player.user.username,
                                  'questions': player.room_open_tasks})
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'group_message',
                    'data': start_event(tasks)
                })
            elif event_type == 'answer':
                for answer in data.get('answer', []):  # update with sql
                    task = UserTaskRoom.objects.get(player=player, room=room, task_id=answer.get('questionId'))
                    task.answer = answer.get('answer')
                    task.status = UserTaskRoom.COMPLETED
                    task.save(update_fields=('answer', 'status'))
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'group_message',
                    'data': answer_accepted_event(player.id, user.username)
                })
                if not room.userroomtasks.filter(status=UserTaskRoom.PENDING):
                    tasks = room.userroomtasks.filter(status=UserTaskRoom.COMPLETED)
                    answers = {}  # optimize with sql or with select related
                    for task in tasks:
                        answer = answers.get(task.task.id)
                        if answer:
                            answer['answers'].append({'userId': task.player_id,
                                                      'username': task.player.user.username,
                                                      'answer': task.answer})
                        else:
                            answers[task.task.id] = {'questionId': task.task.id,
                                                     'question': task.task.title,
                                                     'answers': [{'userId': task.player_id,
                                                                  'username': task.player.user.username,
                                                                  'answer': task.answer}]}
                    async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                        'type': 'group_message',
                        'data': vote_event(list(answers.values()))
                    })
            elif event_type == 'voteList':
                for vote in data.get('votes', []):
                    UserTaskRoom.objects.get(room=room,
                                             task_id=vote.get('questionId'),
                                             player_id=vote.get('voteId')).likes.add(player)
                if room.userroomtasks.filter(status=UserTaskRoom.COMPLETED).aggregate(likes_count=Count('likes'))['likes_count'] == room.players.count() * QUESTION_NUMBER_IN_ROUND:
                    for task in room.tasks.filter(userroomtasks__status=UserTaskRoom.COMPLETED):
                        pair = task.userroomtasks.annotate(likes_count=Count('likes'))
                        obj = max(pair, key=lambda x: x.likes_count)
                        player = obj.player
                        player.score += obj.scope_cost
                        player.save(update_fields=('score',))
                    player = max(room.players.all(), key=lambda x: x.score)
                    async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                        'type': 'group_message',
                        'data': winner_event(player.user.username)
                    })
        except Exception as e:
            print(e)
