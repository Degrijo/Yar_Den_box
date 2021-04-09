from random import shuffle

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.db.models import Count
from rest_framework_simplejwt import authentication

from config.celery import app
from app.core.constants import MIN_PLAYER_NUMBER, SCOPE_ORDER, ANSWERING_DURATION
from app.core.models import Room, PlayerTask, Task, Player
from app.core.tasks import send_delayed_message
from app.core.utils import vote_event, greeting_event, error_event, start_event, define_event, group_by, winner_event, \
    answer_accepted_event, connection_event, score_event, pause_event, resume_event, validate_event, simple_group


# TODO try async consumer
# TODO logging into file


class RoomConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_id = Room.objects.list_actual_rooms().get(name=self.room_name)
        self.room_group_name = 'game_' + self.room_name
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()
        self.send_json(connection_event())

    def disconnect(self, code):
        player = Player.objects.get(id=self.player_id)
        player.active = False
        player.save(update_fields=('active',))
        room = Room.objects.get(id=self.room_id)
        if room.empty:
            room.finish_work()
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive_json(self, data, **kwargs):
        if not validate_event(data):
            self.send_json(error_event("Event isn't valid"))
            return
        print(data)
        event_type = data['eventType']
        try:  # TODO drop in prod
            if event_type == 'pause':
                self.pause()
            elif event_type == 'resume':
                self.resume()
            elif event_type == 'greeting':
                self.greeting(data)
            elif event_type == 'start':
                self.start()
            elif event_type == 'answer':
                self.answer(data)
            elif event_type == 'voteList':
                self.vote(data)
        except Exception as e:
            print(e)

    def send_message(self, event):
        self.send_json(event.get('data'))

    def send_delayed_message(self, event, delay):
        # TODO save task id to db
        task = send_delayed_message.apply_async(args=[self.room_group_name, event], countdown=delay)
        return task

    @staticmethod
    def end_celery_message(task_id):
        app.control.revoke(task_id, terminate=True)

    def pause(self):
        # TODO stop timer
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
            'type': 'send_message',
            'data': pause_event()
        })

    def resume(self):
        # TODO resume timer
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
            'type': 'send_message',
            'data': resume_event()
        })

    def greeting(self, data):
        token = authentication.JWTAuthentication().get_validated_token(data['token'])
        user = authentication.JWTAuthentication().get_user(token)
        player = Player.objects.get(user=user, room_id=self.room_id)
        self.player_id = player.id
        player.socket_channel_name = self.channel_name
        player.active = True
        player.save(update_fields=('socket_channel_name', 'active'))
        room = Room.objects.get(id=self.room_id)
        if room.status == Room.PENDING:
            players = Player.objects.filter(room=room).values('id', 'username')
            self.send_json(define_event(player.id, player.username, player.host))
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                'type': 'send_message',
                'data': greeting_event(room.name, room.password, list(players))
            })
        else:
            data = {}
            if room.status == Room.ANSWERING:
                data = start_event(group_by(player.questions(), 'questions', 'userId', 'username'))
            elif room.status == Room.VOTING:
                data = vote_event(group_by(player.answers(), 'answers', 'questionId', 'question'))
            self.send_json(data)
            if room.paused:
                self.send_json(pause_event())
            # send other reconnection event

    def start(self):
        room = Room.objects.get(id=self.room_id)
        player_count = room.players.count()
        if player_count < MIN_PLAYER_NUMBER:
            self.send_json(error_event('Amount of users smaller than ' + str(MIN_PLAYER_NUMBER)))
            return
        all_tasks = Task.objects.exclude(playertasks__player__room=room)
        if all_tasks.count() < player_count * room.max_round:
            self.send_json(error_event('Not enough tasks for this game'))
            return
        room.start_work()
        game_tasks = all_tasks.order_by('?').values_list('id', flat=True)[:player_count]
        repetitive_tasks = game_tasks.copy()
        repetitive_tasks.append(repetitive_tasks.pop(0))
        players = list(room.players.values_list('id', flat=True))
        shuffle(players)
        scope_cost = room.current_round * (player_count - 1) * SCOPE_ORDER
        for i in range(player_count):
            PlayerTask.objects.create(task_id=game_tasks[i],
                                      player_id=players[i],
                                      round=room.current_round,
                                      scope_cost=scope_cost)
            PlayerTask.objects.create(task_id=repetitive_tasks[i],
                                      player_id=players[i],
                                      round=room.current_round,
                                      scope_cost=scope_cost)
        for channel_name, data in simple_group(room.active_tasks(), 'channel_name'):  # can move to celery
            async_to_sync(self.channel_layer.send)(channel_name, {
                'type': 'send_message',
                'data': start_event(data)
            })
        tasks = room.tasks_for_vote()
        self.send_delayed_message(vote_event(group_by(tasks, 'answers', 'questionId', 'question')), ANSWERING_DURATION)

    def answer(self, data):
        for answer in data['answer']:
            PlayerTask.objects.get(player_id=self.player_id, task_id=answer['questionId']).set_answer(answer['answer'])
        room = Room.objects.get(id=self.room_id)
        players = room.responding_players()
        data = [{'id': player_id, 'username': username} for ch, player_id, username in players]
        for item in players:
            async_to_sync(self.channel_layer.send)(item[0], {
                'type': 'send_message',
                'data': answer_accepted_event(data)
            })
        if not room.has_unfinished_tasks():
            self.end_celery_message(room.timeout_task_id)
            tasks = room.tasks_for_vote(self.player_id)
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                'type': 'send_message',
                'data': vote_event(group_by(tasks, 'answers', 'questionId', 'question'))
            })

    def vote(self, data):
        for vote in data['votes']:
            PlayerTask.objects.get(task_id=vote['questionId'], player_id=vote['voteId']).likes.add(self.player_id)
        room = Room.objects.get(id=self.room_id)
        if room.has_unvoted_tasks():
            for task in Task.objects.filter(playertasks__player__room=room,
                                            userroomtasks__status=PlayerTask.COMPLETED):
                pair = task.playertasks.annotate(likes_count=Count('likes'))
                obj = max(pair, key=lambda x: x.likes_count)
                player = obj.player
                player.score += obj.scope_cost
                player.save(update_fields=('score',))
            if room.current_round == room.max_round:
                player = max(room.players.all(), key=lambda x: x.score)
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'send_message',
                    'data': winner_event(player.user.username)
                })
            else:
                room.current_round += 1
                room.save('current_round')
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
                    'type': 'send_message',
                    'data': score_event(Player.objects.scores(room))
                })
