from string import ascii_uppercase, digits
from random import choices, sample, shuffle

from django.db.models import Count
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, UpdateModelMixin, \
    DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status

from app.core.models import Room, Task, UserRoomTask
from app.core.serializers import PlayerRoomSerializer, HostRoomSerializer, TaskSerializer


class RoomViewSet(GenericViewSet, CreateModelMixin, DestroyModelMixin, RetrieveModelMixin):
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        while True:
            address = ''.join(choices(ascii_uppercase + digits, k=Room._meta.get_field('address').max_length))
            if not Room.objects.filter(address=address).exists():
                break
        room = Room.objects.create(address=address, max_round=request.data['max_round'])
        user = get_user_model().objects.create(username=request.data['username'], room=room, role=get_user_model().HOST)
        if user:
            login(request, user)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='join-room')
    def join_room(self, request, *args, **kwargs):
        room = get_object_or_404(Room, address=request.data['address'])
        if room.status != Room.PENDING:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = get_user_model().objects.create(username=request.data['usernme'], room=room, role=get_user_model().PLAYER)
        if user:
            login(request, user)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='start-game')
    @permission_classes([IsAuthenticated])
    def start_game(self, request):
        if request.user.role != get_user_model().HOST or request.user.room.status == Room.WORKING:
            return Response(status=status.HTTP_400_BAD_REQUEST)
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

    @permission_classes([IsAuthenticated])
    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object().annotate(tasks='userroomtasks__name')

    @permission_classes([IsAuthenticated])
    def destroy(self, request, *args, **kwargs):
        if request.user.role != get_user_model().HOST:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, args, kwargs)
