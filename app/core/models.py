from datetime import datetime, timedelta

from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db.models.manager import Manager
from django.db.models import F, Q, Count
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken, Token

from app.core.constants import PASSWORD_CHARS_NUMBER, DEFAULT_MAX_ROUND, QUESTION_NUMBER_IN_ROUND
from app.core.utils import generate_password
from app.core.validators import CustomUsernameValidator
from app.core.tasks import send_user_confirmation_email, send_user_reset_password_email


# TODO limit CustomToken by timeout, update requirements (django + channels)


class UserManager(BaseUserManager):
    def create_user(self, username, email, password):
        user = self.model(username=username, email=email.lower())
        user.set_password(password)
        user.save(update_fields=('password',))
        send_user_confirmation_email(user.id)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.is_confirmed = True
        user.save(update_fields=('is_superuser', 'is_staff', 'is_confirmed'))
        return user

    def get_user(self, username_or_email):
        return self.filter(is_active=True).filter(Q(username=username_or_email)
                                                  | Q(email=username_or_email.lower())).distinct()

    def list_actual_users(self):
        return self.exclude(is_active=True)


class RoomManager(Manager):
    def list_actual_rooms(self):
        return self.exclude(status=Room.FINISHED)


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

    def is_answer_ends(self, room):  # TODO finish
        return not self.filter(player__room=room, status=PlayerTask.PENDING)

    def is_vote_ends(self, room):  # TODO finish
        return self.filter(room=room, status=PlayerTask.COMPLETED)\
                   .aggregate(likes_count=Count('likes'),
                              filter=Q())\
                   ['likes_count'] == room.players.filter(active=True).count() * QUESTION_NUMBER_IN_ROUND


class CustomUser(AbstractUser):
    rooms = models.ManyToManyField('core.Room', related_name='users', through='core.Player')
    email = models.EmailField()
    username = models.CharField(max_length=150, unique=True, validators=(CustomUsernameValidator,))
    is_confirmed = models.BooleanField(default=False)
    last_login = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    def login_fill(self):
        self.last_login = timezone.now()
        self.save(update_fields=('last_login',))

    def send_confirmation(self):
        send_user_confirmation_email(self.id)

    def send_reset_password(self):
        send_user_reset_password_email(self.id)

    @property
    def tokens_pair(self):
        refresh = RefreshToken.for_user(self)
        access = refresh.access_token
        return {refresh.token_type: refresh, access.token_type: access}

    @property
    def custom_token(self):
        return CustomToken.for_user(self)


class CustomToken(Token):
    token_type = 'custom'
    lifetime = timedelta(seconds=0)


class Pack(models.Model):
    title = models.CharField(max_length=50, unique=True)
    objects = models.Manager()

    class Meta:
        verbose_name = 'Pack'
        verbose_name_plural = 'Packs'

    def __str__(self):
        return self.title


class Task(models.Model):
    title = models.CharField(max_length=500, unique=True)
    pack = models.ForeignKey('core.Pack', on_delete=models.PROTECT, related_name='tasks', blank=True, null=True)
    objects = models.Manager()

    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        return self.title


class Color(models.Model):
    name = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return '#' + self.name


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
    name = models.CharField(max_length=150)
    current_round = models.PositiveSmallIntegerField(default=1)
    max_round = models.PositiveSmallIntegerField(default=DEFAULT_MAX_ROUND)
    status = models.PositiveSmallIntegerField(default=PENDING, choices=STATUS_TYPE)
    private = models.BooleanField(default=True)
    password = models.CharField(max_length=PASSWORD_CHARS_NUMBER, default=generate_password, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    start_work_at = models.DateTimeField(blank=True, null=True)
    finish_work_at = models.DateTimeField(blank=True, null=True)
    objects = RoomManager()

    class Meta:
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'

    def __str__(self):
        return self.name

    @property
    def random_player_color(self):
        return Color.objects.exclude(players__room=self).order_by('?')[0]

    @property
    def empty(self):
        return self.players.filter(active=True).exists()

    def is_has_user(self, user):
        return self.players.filter(user=user).exists()

    def start_work(self):
        self.status = self.WORKING
        self.start_work_at = timezone.now()
        self.save(update_fields=('status', 'start_work_at'))

    def finish_work(self):
        self.status = self.FINISHED
        self.finish_work_at = timezone.now()
        self.save(update_fields=('status', 'finish_work_at'))

    def check_password(self, password):
        return self.password == password


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
        verbose_name = 'Player'
        verbose_name_plural = 'Players'

    def __str__(self):
        return f'{self.username} on room "{self.room.name}"'


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
    created_at = models.DateTimeField(default=timezone.now)
    answered_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    objects = PlayerTaskManager()

    class Meta:
        verbose_name = 'Own task'
        verbose_name_plural = 'Own tasks'

    def set_answer(self, answer):
        self.answer = answer
        self.status = self.COMPLETED
        self.answered_at = timezone.now()
        self.save(update_fields=('answer', 'status', 'answered_at'))

    def finish(self):
        self.status = self.FINISHED
        self.finished_at = timezone.now()
        self.save(update_fields=('status', 'answered_at'))
