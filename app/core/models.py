from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model


class CustomUser(AbstractUser):
    HOST = 0
    PLAYER = 1
    ROLE_TYPES = (
        (HOST, 'Host'),
        (PLAYER, 'Player')
    )
    first_name = None
    last_name = None
    email = None
    password = None
    role = models.PositiveSmallIntegerField(default=PLAYER, choices=ROLE_TYPES)
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='users')
    tasks = models.ManyToManyField('Task', related_name='users', through='UserTask')
    score = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.username


class Room(models.Model):
    PENDING = 0
    WORKING = 1
    STATUS_TYPE = (
        (PENDING, 'Pending'),
        (WORKING, 'Working')
    )
    address = models.CharField(max_length=4, unique=True)
    current_round = models.PositiveSmallIntegerField(default=1)
    max_round = models.PositiveSmallIntegerField(default=3)
    status = models.PositiveSmallIntegerField(default=PENDING)
    objects = models.Manager()

    def __str__(self):
        return self.address


class Task(models.Model):
    name = models.CharField(max_length=500, unique=True)
    image = models.ImageField(blank=True, null=True)
    objects = models.Manager()

    def __str__(self):
        return self.name


class UserTask(models.Model):
    PENDING = 0
    COMPLETED = 1
    FINISHED = 2
    STATUS_TYPES = (
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FINISHED, 'Finished')
    )
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='usertasks')
    # room = models.ForeignKey('Room', on_delete=models.CASCADE, 'userroomtasks')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='usertasks')
    answer = models.CharField(max_length=500, blank=True)
    likes = models.ManyToManyField(get_user_model(), related_name='liked_answers')
    status = models.PositiveSmallIntegerField(default=PENDING)
    scope_cost = models.PositiveSmallIntegerField()
    objects = models.Manager()
