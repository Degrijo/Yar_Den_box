from django.contrib.auth import get_user_model

from rest_framework import serializers

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


class HostRoomSerializer(serializers.ModelSerializer):
    address = serializers.CharField(max_length=4, source='room.address', read_only=True)
    current_round = serializers.IntegerField(allow_null=True, source='room.current_round', read_only=True)
    max_round = serializers.IntegerField(allow_null=True, source='room.max_round')

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


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'name', 'image')


# class RoomSerializer(serializers.ModelSerializer):
#     tasks = TaskSerializer(many=True)
#
#     class Meta:
#         model = Room
#         fields = ('id', 'current_task', 'tasks')
#
#     def get_tasks(self, obj):  # "Do anything": {'user1': ''}
#         return obj.tasks.annotate()


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


class VoitingSerializer(serializers.ModelSerializer):  # set voite
    likes = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserTaskRoom
        fields = ('id', 'likes')
