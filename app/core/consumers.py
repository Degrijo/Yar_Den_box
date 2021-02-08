import json
from random import sample, shuffle

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db.models import F, Count, Q
from rest_framework_simplejwt import authentication

from app.core.models import Room, UserTaskRoom, Task, Player
from app.core.utils import vote_event, greeting_event, error_event, start_event, define_event, group_by, winner_event,\
    answer_accepted_event, connection_event
# for speed can store ids, not orm obj

QUESTION_NUMBER_IN_ROUND = 2
MIN_PLAYER_NUMBER = 2
SCOPE_ORDER = 10


class RoomConsumer(WebsocketConsumer):
    def connect(self):
        room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'game_' + room_name
        self.room = Room.objects.get(name=room_name)
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
            if event_type == 'greeting':
                token = authentication.JWTAuthentication().get_validated_token(data.get('token'))
                self.user = authentication.JWTAuthentication().get_user(token)
                self.player = Player.objects.get(user=self.user, room=self.room)
                players = Player.objects.filter(room=self.room).values('id', username=F('user__username'))
                self.send(define_event(self.player.id, self.user.username, self.player.host))
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'group_message',
                    'data': greeting_event(list(players))
                })
            elif event_type == 'start':
                player_count = self.room.players.count()
                if player_count < MIN_PLAYER_NUMBER:
                    self.send(error_event('Amount of users smaller than ' + str(MIN_PLAYER_NUMBER)))
                    return
                all_tasks = Task.objects.exclude(rooms__id=self.room.id)
                if all_tasks.count() < player_count:
                    self.send({'event_type': 'error',
                               'message': 'Task counter should be bigger or equal than user counter'})
                    return
                self.room.status = Room.WORKING
                self.room.save(update_fields=('status',))
                if self.room.players.annotate(task_count=Count('userroomtasks',
                                              filter=Q(userroomtasks__status=UserTaskRoom.PENDING)))\
                                    .filter(task_count__lt=QUESTION_NUMBER_IN_ROUND):  # check with completed usertaskrooms
                    game_tasks = sample(list(all_tasks.values_list('id', flat=True)), k=player_count)
                    repetitive_tasks = game_tasks.copy()
                    repetitive_tasks.append(repetitive_tasks.pop(0))
                    players = list(self.room.players.values_list('id', flat=True))
                    shuffle(players)
                    scope_cost = self.room.current_round * (player_count - 1) * SCOPE_ORDER
                    for i in range(player_count):
                        UserTaskRoom.objects.create(task_id=game_tasks[i],
                                                    player_id=players[i],
                                                    room=self.room,
                                                    scope_cost=scope_cost)
                        UserTaskRoom.objects.create(task_id=repetitive_tasks[i],
                                                    player_id=players[i],
                                                    room=self.room,
                                                    scope_cost=scope_cost)
                tasks = UserTaskRoom.objects.filter(room=self.room, status=UserTaskRoom.PENDING) \
                                            .select_related('player', 'player__user', 'task') \
                                            .values(userId=F('player_id'),
                                                    username=F('player__user__username'),
                                                    questionId=F('task_id'),
                                                    text=F('task__title'))
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'group_message',
                    'data': start_event(group_by(tasks, 'questions', 'userId', 'username'))
                })
            elif event_type == 'answer':
                for answer in data.get('answer', []):  # update with sql
                    task = UserTaskRoom.objects.get(player=self.player, room=self.room, task_id=answer.get('questionId'))
                    task.answer = answer.get('answer')
                    task.status = UserTaskRoom.COMPLETED
                    task.save(update_fields=('answer', 'status'))
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'group_message',
                    'data': answer_accepted_event(self.player.id, self.user.username)
                })
                if not self.room.userroomtasks.filter(status=UserTaskRoom.PENDING):
                    tasks = UserTaskRoom.objects.filter(room=self.room, status=UserTaskRoom.COMPLETED) \
                                                .select_related('task', 'player', 'player__user') \
                                                .values('answer',
                                                        questionId=F('task_id'),
                                                        question=F('task__title'),
                                                        userID=F('player_id'),
                                                        username=F('player__user__username'))
                    async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                        'type': 'group_message',
                        'data': vote_event(group_by(tasks, 'answers', 'questionId', 'question'))
                    })
            elif event_type == 'voteList':
                for vote in data.get('votes', []):
                    UserTaskRoom.objects.get(room=self.room,
                                             task_id=vote.get('questionId'),
                                             player_id=vote.get('voteId')).likes.add(self.player)
                if self.room.userroomtasks.filter(status=UserTaskRoom.COMPLETED).aggregate(likes_count=Count('likes'))['likes_count'] == self.room.players.count() * QUESTION_NUMBER_IN_ROUND:
                    for task in self.room.tasks.filter(userroomtasks__status=UserTaskRoom.COMPLETED):
                        pair = task.userroomtasks.annotate(likes_count=Count('likes'))
                        obj = max(pair, key=lambda x: x.likes_count)
                        player = obj.player
                        player.score += obj.scope_cost
                        player.save(update_fields=('score',))
                    player = max(self.room.players.all(), key=lambda x: x.score)
                    async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                        'type': 'group_message',
                        'data': winner_event(player.user.username)
                    })
        except Exception as e:
            print(e)
