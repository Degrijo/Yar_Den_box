from django.db import models
from django.contrib.auth.models import AbstractUser


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
    tasks = models.ManyToManyField('Task', related_name='rooms', through='UserRoomTask')
    objects = models.Manager()

    def __str__(self):
        return self.address


class Task(models.Model):
    name = models.CharField(max_length=500)
    image = models.ImageField(blank=True, null=True)
    objects = models.Manager()

    def __str__(self):
        return self.name


class UserRoomTask(models.Model):
    PENDING = 0
    COMPLETED = 1
    FINISHED = 2
    STATUS_TYPES = (
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FINISHED, 'Finished')
    )
    task = models.ForeignKey('Task', models.PROTECT, 'userroomtasks')
    room = models.ForeignKey('Room', models.CASCADE, 'userroomtasks')
    user = models.ForeignKey('CustomUser', models.PROTECT, 'userroomtasks')
    answer = models.CharField(max_length=500, blank=True)
    status = models.PositiveSmallIntegerField(default=PENDING)
