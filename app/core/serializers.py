from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator

from rest_framework import serializers

from app.core.models import Room, Task


class HostRoomSerializer(serializers.ModelSerializer):
    address = serializers.CharField(max_length=4, source='room.username', read_only=True)
    current_round = serializers.IntegerField(default=1, source='room.current_round', read_only=True)
    max_round = serializers.IntegerField(default=3, source='room.max_round')

    class Meta:
        model = get_user_model()
        fields = ('id', 'address', 'current_round', 'max_round', 'username')
        read_only_fields = ('id',)


class PlayerRoomSerializer(serializers.ModelSerializer):
    address = serializers.CharField(max_length=4, source='room.address')

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'address')
        read_only_fields = ('id',)


class RoomSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ('id', 'current_task', 'tasks')

    def get_tasks(self, obj):  # "Do anything": {'user1': ''}
        obj.tasks.annotate()


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('name', 'image')
