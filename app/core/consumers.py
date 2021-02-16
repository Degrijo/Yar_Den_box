import json
from random import sample, shuffle

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.db.models import F, Count
from rest_framework_simplejwt import authentication

from app.core.models import Room, PlayerTask, Task, Player
from app.core.utils import vote_event, greeting_event, error_event, start_event, define_event, group_by, winner_event, \
    answer_accepted_event, connection_event, score_event

# for speed can store ids, not orm obj

MIN_PLAYER_NUMBER = 2
SCOPE_ORDER = 10


class RoomConsumer(JsonWebsocketConsumer):
    def connect(self):
        room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + room_name
        self.room = Room.objects.get(name=room_name)
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()
        self.send_json(connection_event())

    def disconnect(self, code):
        self.player.active = False
        self.player.save(update_fields=('active',))
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def send_message(self, event):
        self.send_json(event.get('data'))

    def receive_json(self, data, **kwargs):
        try:
            print(data)
            event_type = data.get('eventType')
            if event_type == 'greeting':
                token = authentication.JWTAuthentication().get_validated_token(data.get('token'))
                self.user = authentication.JWTAuthentication().get_user(token)
                self.player = Player.objects.get(user=self.user, room=self.room)
                self.player.socket_channel_name = self.channel_name
                self.player.active = True
                self.player.save(update_fields=('socket_channel_name', 'active'))
                if self.room.status == Room.PENDING:
                    players = Player.objects.filter(room=self.room).values('id', username=F('user__username'))
                    self.send_json(define_event(self.player.id, self.user.username, self.player.host))
                    async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                        'type': 'send_message',
                        'data': greeting_event(list(players))
                    })
                else:
                    data = {}
                    if self.room.status == Room.ANSWERING:
                        tasks = PlayerTask.objects.player_for_answer(self.player)
                        data = start_event(group_by(tasks, 'questions', 'userId', 'username'))
                    elif self.room.status == Room.VOTING:
                        tasks = PlayerTask.objects.player_for_vote(self.player)
                        data = vote_event(group_by(tasks, 'answers', 'questionId', 'question'))
                    self.send_json(data)
                    # send other reconnection event
            elif event_type == 'start':
                player_count = self.room.players.count()
                if player_count < MIN_PLAYER_NUMBER:
                    self.send_json(error_event('Amount of users smaller than ' + str(MIN_PLAYER_NUMBER)))
                    return
                all_tasks = Task.objects.exclude(rooms__id=self.room.id)
                if all_tasks.count() < player_count:
                    self.send_json(error_event('Task counter should be bigger or equal than user counter'))
                    return
                self.room.status = Room.ANSWERING
                self.room.save(update_fields=('status',))
                if PlayerTask.objects.no_unanswered(self.room):  # check time
                    game_tasks = sample(list(all_tasks.values_list('id', flat=True)), k=player_count)
                    repetitive_tasks = game_tasks.copy()
                    repetitive_tasks.append(repetitive_tasks.pop(0))
                    players = list(self.room.players.values_list('id', flat=True))
                    shuffle(players)
                    scope_cost = self.room.current_round * (player_count - 1) * SCOPE_ORDER
                    for i in range(player_count):
                        PlayerTask.objects.create(task_id=game_tasks[i],
                                                  player_id=players[i],
                                                  scope_cost=scope_cost)
                        PlayerTask.objects.create(task_id=repetitive_tasks[i],
                                                  player_id=players[i],
                                                  scope_cost=scope_cost)
                tasks = PlayerTask.objects.room_for_answer(self.room)
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'send_message',
                    'data': start_event(group_by(tasks, 'questions', 'userId', 'username'))
                })
            elif event_type == 'answer':
                for answer in data.get('answer', []):  # update with sql
                    task = PlayerTask.objects.get(player=self.player, task_id=answer.get('questionId'))
                    task.answer = answer.get('answer')
                    task.status = PlayerTask.COMPLETED
                    task.save(update_fields=('answer', 'status'))
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'send_message',
                    'data': answer_accepted_event(self.player.id, self.user.username)
                })
                if not PlayerTask.objects.is_answer_ends():  # check timeout
                    tasks = PlayerTask.objects.room_vote(self.room)
                    async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                        'type': 'send_message',
                        'data': vote_event(group_by(tasks, 'answers', 'questionId', 'question'))
                    })
            elif event_type == 'voteList':
                for vote in data.get('votes', []):
                    PlayerTask.objects.get(task_id=vote.get('questionId'),
                                           player_id=vote.get('voteId')).likes.add(self.player)
                if PlayerTask.objects.is_vote_ends(self.room):  # check timeout
                    for task in self.room.tasks.filter(userroomtasks__status=PlayerTask.COMPLETED):
                        pair = task.playertasks.annotate(likes_count=Count('likes'))
                        obj = max(pair, key=lambda x: x.likes_count)
                        player = obj.player
                        player.score += obj.scope_cost
                        player.save(update_fields=('score',))
                    if self.room.current_round == self.room.max_round:
                        player = max(self.room.players.all(), key=lambda x: x.score)
                        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                            'type': 'send_message',
                            'data': winner_event(player.user.username)
                        })
                    else:
                        self.room.current_round += 1
                        self.room.save('current_round')
                        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                            'type': 'send_message',
                            'data': score_event(Player.objects.scores(self.room))
                        })
        except Exception as e:
            print(e)
