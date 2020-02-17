from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Count


class CustomUser(AbstractUser):
    WATCHER = 0
    PLAYER = 1
    CAPTIVER = 2
    ROLE_TYPES = (
        (WATCHER, 'Watcher'),
        (PLAYER, 'Player'),
        (CAPTIVER, 'Captiver')
    )
    OPEN_ROLE_TYPES = (
        (WATCHER, 'Watcher'),
        (PLAYER, 'Player'),
    )
    first_name = None
    last_name = None
    email = None
    rooms = models.ManyToManyField('Room', related_name='users', through='UserRoom')
    watchers_room = models.ForeignKey('Room', on_delete=models.SET_NULL, related_name='watchers', null=True, blank=True)
    players_room = models.OneToOneField('Room', on_delete=models.SET_NULL, related_name='player', null=True, blank=True)
    role = models.PositiveSmallIntegerField(default=WATCHER, choices=OPEN_ROLE_TYPES)


class Room(models.Model):
    address = models.CharField(max_length=4, unique=True)
    objects = models.Manager()

    def __str__(self):
        return self.address


class UserRoom(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='userrooms')
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='userrooms')
    favorite = models.BooleanField(default=False)
    donated = models.DecimalField(max_digits=20, decimal_places=2)
    objects = models.Manager()


class Task(models.Model):
    FAILURE_VIOLATION = 0
    DELATION_VIOLATION = 1
    VIOLATION_TYPES = (
        (FAILURE_VIOLATION, 'Failure'),
        (DELATION_VIOLATION, 'Delation')
    )
    PROPOSED_STATUS = 0
    APPROVED_STATUS = 1
    DONE_STATUS = 2
    DISTURBED_STATUS = 3
    STATUS_TYPES = (
        (PROPOSED_STATUS, 'Proposed'),
        (APPROVED_STATUS, 'Approved'),
        (DONE_STATUS, 'Done'),
        (DISTURBED_STATUS, 'Disturbed')
    )
    name = models.CharField(max_length=200)
    status = models.PositiveSmallIntegerField(default=PROPOSED_STATUS, choices=STATUS_TYPES)
    violation = models.PositiveSmallIntegerField(blank=True, null=True, choices=VIOLATION_TYPES)
    prize = models.DecimalField(max_digits=20, decimal_places=2)
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='tasks')
    objects = models.Manager()
