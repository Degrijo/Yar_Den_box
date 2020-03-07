from string import ascii_uppercase, digits
from random import choices, sample, shuffle

from django.contrib.auth import login, logout, get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, UpdateModelMixin, \
    DestroyModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework import status

from app.core.models import Room, Task, UserRoomTask
from app.core.serializers import PlayerRoomSerializer, HostRoomSerializer, TaskSerializer
from app.core.permissions import HostPermission, PlayerPermission, WorkingRoomPermission, PendingRoomPermission


class GameViewSet(GenericViewSet, CreateModelMixin, DestroyModelMixin, RetrieveModelMixin):
    queryset = Room.objects.all()

    def get_queryset(self):
        if self.action == 'join_room':
            return get_user_model().objects.all()
        return Room.objects.all()

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'create':
            return HostRoomSerializer
        elif self.action == 'get_current_task':
            return TaskSerializer
        elif self.action == 'join_room':
            return PlayerRoomSerializer

    @permission_classes([AllowAny])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        while True:
            address = ''.join(choices(ascii_uppercase + digits, k=Room._meta.get_field('address').max_length))
            if not Room.objects.filter(address=address).exists():
                break
        room = Room.objects.create(address=address, max_round=request.data['max_round'])
        user = get_user_model().objects.create(username=request.data['username'], room=room, role=get_user_model().HOST)
        login(request, user)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='join-room')
    @permission_classes([AllowAny])
    def join_room(self, request, *args, **kwargs):
        room = get_object_or_404(Room, address=request.data['address'])
        if room.status != Room.PENDING:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = get_user_model().objects.create(username=request.data['usernme'], room=room, role=get_user_model().PLAYER)
        login(request, user)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='start-game')
    @permission_classes([HostPermission, PendingRoomPermission])
    def start_game(self, request):
        room = request.user.room
        user_count = room.users.count()
        if user_count < 2:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        tasks = Task.objects.exclude(rooms__id=room.id)
        if tasks.count() < user_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        room.status = Room.WORKING
        room.save()
        game_tasks = shuffle(sample(list(tasks.values('id')), k=user_count) * 2)
        for i in range(user_count):
            UserRoomTask.objects.create(task_id=game_tasks[2*i], room=room, user=room.users[i], status=UserRoomTask.PENDING)
            UserRoomTask.objects.create(task_id=game_tasks[2*i + 1], room=room, user=room.users[i], status=UserRoomTask.PENDING)
        return Response(status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='get-task')
    @permission_classes([WorkingRoomPermission])
    def get_task(self, request):
        return Task.objects.filter(userroomtask__status=UserRoomTask.PENDING, userroomtask__user=request.user, userroomtask__room=)

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object().annotate(tasks='userroomtasks__name')

    @permission_classes([HostPermission])
    def destroy(self, request, *args, **kwargs):
        logout(request)  # should logout all users?
        return super().destroy(request, args, kwargs)
