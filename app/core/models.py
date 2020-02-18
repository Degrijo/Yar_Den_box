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

    def __str__(self):
        return self.username


class Room(models.Model):
    address = models.CharField(max_length=4, unique=True)
    current_round = models.PositiveSmallIntegerField()
    max_round = models.PositiveSmallIntegerField()
    objects = models.Manager()

    def __str__(self):
        return self.address


class Task(models.Model):
    name = models.CharField(max_length=500)
    image = models.ImageField()
    objects = models.Manager()

    def __str__(self):
        return self.name


class UserRoomTask(models.Model):
    task = models.ForeignKey('Task', models.CASCADE, 'userroomtasks')
    room = models.ForeignKey('Room', models.CASCADE, 'userroomtasks')
    user = models.ForeignKey('CustomUser', models.CASCADE, 'userroomtasks')
    answer = models.CharField(max_length=500)
