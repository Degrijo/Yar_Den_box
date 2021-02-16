from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db.models.manager import Manager
from django.db.models import F, Q, Count

from app.core.constants import PASSWORD_CHARS_NUMBER, DEFAULT_MAX_ROUND
from app.core.utils import generate_password


QUESTION_NUMBER_IN_ROUND = 2


class RoomQuerySet(models.query.QuerySet):
    def delete(self):
        for room in self:
            archived_room = ArchivedRoom.objects.create(**room.archived_data)
            for player in room.players.all():
                ArchivedPlayer.objects.create(**player.archived_data, room=archived_room)
                for player_task in player.playertasks.all():
                    ArchivedPlayerTask.objects.create(**player_task.archived_data, player=player)
        return super().delete()


class PlayerManager(Manager):
    def room_inf(self, room):
        return self.filter(room=room).values('id', username=F('username'))

    def is_has_duple_tasks(self, room):
        return self.filter(room=room, active=True)\
                   .annotate(task_count=Count('playertasks', filter=Q(playertasks__status=PlayerTask.PENDING))) \
                   .filter(task_count__lt=QUESTION_NUMBER_IN_ROUND)  # check with completed playertasks

    def scores(self, room):
        return self.filter(room=room).values(userId=F('id'), username=F('username'), score=F('score'))


class PlayerTaskManager(Manager):
    def room_answer(self, room):
        return self.filter(player__room=room, status=PlayerTask.PENDING) \
                   .select_related('player', 'task') \
                   .values(userId=F('player_id'),
                           username=F('player__username'),
                           questionId=F('task_id'),
                           text=F('task__title'))

    def player_answer(self, player):
        return self.filter(player=player, status=PlayerTask.PENDING) \
                   .select_related('task') \
                   .values(questionId=F('task_id'),
                           text=F('task__title'))

    def room_vote(self, room):
        return self.filter(player__room=room, status=PlayerTask.COMPLETED) \
                   .select_related('task', 'player') \
                   .values('answer',
                           questionId=F('task_id'),
                           question=F('task__title'),
                           userID=F('player_id'),
                           username=F('player__username'))

    def player_vote(self, player):
        return self.filter(player=player, status=PlayerTask.COMPLETED) \
                   .select_related('task') \
                   .values('answer',
                           questionId=F('task_id'),
                           question=F('task__title'))

    def is_answer_ends(self, room):
        return not self.filter(player__room=room, status=PlayerTask.PENDING)

    def is_vote_ends(self, room):  # need update
        return self.filter(room=room, status=PlayerTask.COMPLETED).aggregate(likes_count=Count('likes'), filter=Q())[
            'likes_count'] == room.players.filter(active=True).count() * QUESTION_NUMBER_IN_ROUND


class RoomManager(Manager):
    _queryset_class = RoomQuerySet


class CustomUser(AbstractUser):
    rooms = models.ManyToManyField('core.Room', related_name='users', through='core.Player')
    email = models.EmailField(unique=True,
                              error_messages={
                                    'unique': "A user with that username already exists."
                                }
                              )
    male = models.BooleanField()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username


class Pack(models.Model):
    title = models.CharField(max_length=50, unique=True)
    objects = models.Manager()

    class Meta:
        verbose_name = "Pack"
        verbose_name_plural = "Packs"

    def __str__(self):
        return self.title


class Task(models.Model):
    title = models.CharField(max_length=500, unique=True)
    pack = models.ForeignKey('core.Pack', on_delete=models.PROTECT, related_name='tasks', blank=True, null=True)
    objects = models.Manager()

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title


class Color(models.Model):
    name = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return '#' + self.name


class ArchivedRoom(models.Model):
    name = models.CharField(max_length=150)
    current_round = models.PositiveSmallIntegerField()
    max_round = models.PositiveSmallIntegerField()
    private = models.BooleanField()
    created_at = models.DateTimeField()
    start_work_at = models.DateTimeField()
    finished_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        verbose_name = "Archived room"
        verbose_name_plural = "Archived rooms"


class Room(models.Model):
    PENDING = 0
    WORKING = 1
    ANSWERING = 2
    VOTING = 3
    FINISHED = 4
    STATUS_TYPE = (
        (PENDING, 'Pending'),
        (WORKING, 'Working'),
        (ANSWERING, 'Answering'),
        (VOTING, 'Voting'),
        (FINISHED, 'Finished')
    )
    name = models.CharField(max_length=150, unique=True)
    current_round = models.PositiveSmallIntegerField(default=1)
    max_round = models.PositiveSmallIntegerField(default=DEFAULT_MAX_ROUND)
    status = models.PositiveSmallIntegerField(default=PENDING, choices=STATUS_TYPE)
    private = models.BooleanField(default=False)
    password = models.CharField(max_length=PASSWORD_CHARS_NUMBER, default=generate_password, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_work_at = models.DateTimeField(blank=True, null=True)
    objects = RoomManager()

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self):
        return self.name

    @property
    def random_player_color(self):
        return Color.objects.exclude(players__room=self).order_by('?')[0]

    @property
    def archived_data(self):
        return {'name': self.name, 'current_round': self.current_round, 'max_round': self.max_round,
                'private': self.private, 'created_at': self.created_at, 'start_work_at': self.start_work_at}

    def is_has_user(self, user):
        return self.players.filter(user=user).exists()

    def start_work(self):
        self.status = self.WORKING
        self.start_work_at = datetime.now()
        self.save(update_fields=('status', 'start_work_at'))

    def check_password(self, password):
        return self.password == password


class ArchivedPlayer(models.Model):
    username = models.CharField(max_length=150)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='archived_players')
    room = models.ForeignKey('core.ArchivedRoom', on_delete=models.CASCADE, related_name='archived_players')
    host = models.BooleanField()
    score = models.PositiveSmallIntegerField()
    color = models.ForeignKey('core.Color', on_delete=models.CASCADE, related_name='archived_players')
    objects = models.Manager()

    class Meta:
        verbose_name = "Archived player"
        verbose_name_plural = "Archived players"


class Player(models.Model):
    username = models.CharField(max_length=150)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='players')
    room = models.ForeignKey('core.Room', on_delete=models.CASCADE, related_name='players')
    host = models.BooleanField(default=False)
    score = models.PositiveSmallIntegerField(default=0)
    socket_channel_name = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=False)
    color = models.ForeignKey('core.Color', on_delete=models.CASCADE, related_name='players')
    objects = PlayerManager()

    class Meta:
        verbose_name = "Player"
        verbose_name_plural = "Players"
        unique_together = ('username', 'room')

    def __str__(self):
        return f'{self.username} on room "{self.room.name}"'

    @property
    def archived_data(self):
        return {'username': self.username, 'user': self.user, 'host': self.host, 'score': self.score,
                'color': self.color}


class ArchivedPlayerTask(models.Model):
    task = models.ForeignKey('core.Task', on_delete=models.CASCADE, related_name='archived_playertasks')
    player = models.ForeignKey('core.ArchivedPlayer', on_delete=models.CASCADE, related_name='archived_playertasks')
    answer = models.CharField(max_length=500, blank=True)
    likes = models.PositiveSmallIntegerField()
    scope_cost = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField()
    answered_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    objects = models.Manager()

    class Meta:
        verbose_name = "Archived own task"
        verbose_name_plural = "Archived own tasks"


class PlayerTask(models.Model):
    PENDING = 0
    COMPLETED = 1
    FINISHED = 2
    STATUS_TYPES = (
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FINISHED, 'Finished')
    )
    task = models.ForeignKey('core.Task', on_delete=models.CASCADE, related_name='playertasks')
    player = models.ForeignKey('core.Player', on_delete=models.CASCADE, related_name='playertasks')
    answer = models.CharField(max_length=500, blank=True)
    likes = models.ManyToManyField('core.Player', related_name='liked_answers')
    status = models.PositiveSmallIntegerField(default=PENDING, choices=STATUS_TYPES)
    scope_cost = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    objects = PlayerTaskManager()

    class Meta:
        verbose_name = "Own task"
        verbose_name_plural = "Own tasks"

    @property
    def archived_data(self):
        return {'task': self.task, 'answer': self.answer, 'scope_cost': self.scope_cost, 'created_at': self.created_at,
                'answered_at': self.answered_at, 'finished_at': self.finished_at, 'likes': self.likes.count()}

    def set_answer(self, answer):
        self.answer = answer
        self.status = self.COMPLETED
        self.answered_at = datetime.now()
        self.save(update_fields=('answer', 'status', 'answered_at'))

    def finish(self):
        self.status = self.FINISHED
        self.finished_at = datetime.now()
        self.save(update_fields=('status', 'answered_at'))
