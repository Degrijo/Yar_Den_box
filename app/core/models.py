from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model


class CustomUser(AbstractUser):
    OBSERVER = 0
    HOST = 1
    PLAYER = 2
    ROLE_TYPES = (
        (OBSERVER, 'Observer'),
        (HOST, 'Host'),
        (PLAYER, 'Player'),
    )
    role = models.PositiveSmallIntegerField(default=OBSERVER, choices=ROLE_TYPES)
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='users')
    score = models.PositiveSmallIntegerField(default=0)

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
    address = models.CharField(max_length=4, unique=True)
    current_round = models.PositiveSmallIntegerField(default=1)
    max_round = models.PositiveSmallIntegerField(default=3)
    status = models.PositiveSmallIntegerField(default=PENDING)
    objects = models.Manager()

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self):
        return self.address


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
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT, related_name='tasks')
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
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='userroomtasks')
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='userroomtasks')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='userroomtasks')
    answer = models.CharField(max_length=500, blank=True)
    likes = models.ManyToManyField(get_user_model(), related_name='liked_answers')
    status = models.PositiveSmallIntegerField(default=PENDING)
    scope_cost = models.PositiveSmallIntegerField()
    objects = models.Manager()

    class Meta:
        verbose_name = "Own task"
        verbose_name_plural = "Own tasks"
