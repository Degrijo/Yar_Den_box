from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model


class CustomUser(AbstractUser):
    rooms = models.ManyToManyField('core.Room', related_name='users', through='core.Player')

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username


class Room(models.Model):
    PENDING = 0
    WORKING = 1
    FINISHED = 2
    STATUS_TYPE = (
        (PENDING, 'Pending'),
        (WORKING, 'Working'),
        (FINISHED, 'Finished')
    )
    name = models.CharField(max_length=150, unique=True)
    current_round = models.PositiveSmallIntegerField(default=1)
    max_round = models.PositiveSmallIntegerField(default=3)
    status = models.PositiveSmallIntegerField(default=PENDING, choices=STATUS_TYPE)
    tasks = models.ManyToManyField('core.Task', related_name='rooms', through='UserTaskRoom')
    objects = models.Manager()

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self):
        return self.name


class Player(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='players')
    room = models.ForeignKey('core.Room', on_delete=models.CASCADE, related_name='players')
    host = models.BooleanField(default=False)
    score = models.PositiveSmallIntegerField(default=0)


class Tag(models.Model):
    title = models.CharField(max_length=50, unique=True)
    objects = models.Manager()

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.title


class Task(models.Model):
    title = models.CharField(max_length=500, unique=True)
    tag = models.ForeignKey('core.Tag', on_delete=models.PROTECT, related_name='tasks', blank=True, null=True)
    objects = models.Manager()

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title


class UserTaskRoom(models.Model):
    PENDING = 0
    COMPLETED = 1
    FINISHED = 2
    STATUS_TYPES = (
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FINISHED, 'Finished')
    )
    task = models.ForeignKey('core.Task', on_delete=models.CASCADE, related_name='userroomtasks')
    room = models.ForeignKey('core.Room', on_delete=models.CASCADE, related_name='userroomtasks')
    player = models.ForeignKey('core.Player', on_delete=models.CASCADE, related_name='userroomtasks')
    answer = models.CharField(max_length=500, blank=True)
    likes = models.ManyToManyField(get_user_model(), related_name='liked_answers')
    status = models.PositiveSmallIntegerField(default=PENDING)
    scope_cost = models.PositiveSmallIntegerField()
    objects = models.Manager()

    class Meta:
        verbose_name = "Own task"
        verbose_name_plural = "Own tasks"
