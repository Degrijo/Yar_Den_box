from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.authtoken.models import Token

from app.core.models import Room, Task, UserTaskRoom


class SigUpSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')


class LogInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128)

    class Meta:
        fields = ('username', 'password')


class CreateGameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = ('name', 'max_round')


class ConnectGameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = ('name',)


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'name')


class AnswerSerializer(serializers.ModelSerializer):  # set answer
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    status = serializers.HiddenField(default=UserTaskRoom.COMPLETED)

    class Meta:
        model = UserTaskRoom
        fields = ('user', 'task_id', 'answer', 'status')


class CompletedTaskSerializer(serializers.ModelSerializer):
    task = serializers.CharField(max_length=500, source='task.name')
    user = serializers.CharField(source='user.username')

    class Meta:
        model = UserTaskRoom
        fields = ('id', 'task', 'answer', 'user')


class VoiteSerializer(serializers.ModelSerializer):  # set voite
    likes = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserTaskRoom
        fields = ('id', 'likes')


class ListRoomSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(min_value=0)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ('name', 'capacity', 'current_round', 'max_round', 'status')

    def get_status(self, obj):
        return dict(obj.STATUS_TYPE).get(obj.status)


class RoomSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ('name', 'current_round', 'users')

    def get_users(self, obj):
        return obj.users.values_list('username', flat=True)


class VoitingSerializer(serializers.ModelSerializer):

    class Model:
        model = UserTaskRoom
        fields = ('id', 'likes')
