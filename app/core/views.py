from string import ascii_uppercase, digits
from random import choices, sample, shuffle

from django.contrib.auth import login, logout, get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, UpdateModelMixin, \
    DestroyModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework import status

from app.core.models import Room, Task, UserTask
from app.core.serializers import PlayerRoomSerializer, HostRoomSerializer, TaskSerializer, AnswerSerializer, VoitingSerializer
from app.core.permissions import HostPermission, PlayerPermission, WorkingRoomPermission, PendingRoomPermission


class GameViewSet(GenericViewSet, CreateModelMixin, DestroyModelMixin, RetrieveModelMixin):
    queryset = Room.objects.all()

    def get_queryset(self):
        if self.action == 'join-room':
            return get_user_model().objects.all()
        elif self.action == 'set-answer':
            return UserTask.objects.all()
        return Room.objects.all()

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'create':
            return HostRoomSerializer
        elif self.action == 'get_task':
            return TaskSerializer
        elif self.action == 'join_room':
            return PlayerRoomSerializer
        elif self.action == 'set_answer':
            return AnswerSerializer
        elif self.action == 'set_voite':
            return VoitingSerializer

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
            return Response(data='The game started yet', status=status.HTTP_400_BAD_REQUEST)
        user = get_user_model().objects.create(username=request.data['username'], room=room, role=get_user_model().PLAYER)
        login(request, user)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False, url_path='start-game')
    @permission_classes([HostPermission, PendingRoomPermission])
    def start_game(self, request):
        room = request.user.room
        user_count = room.users.count()
        if user_count < 3:
            return Response(data='Counter of user smaller than 3', status=status.HTTP_400_BAD_REQUEST)
        tasks = Task.objects.exclude(users__room__id=room.id)
        if tasks.count() < user_count:
            return Response(data='Task counter should be bigger or equal than user counter', status=status.HTTP_204_NO_CONTENT)
        room.status = Room.WORKING
        room.save()
        game_tasks = sample(list(tasks.values_list('id', flat=True)), k=user_count)
        repetitive_tasks = game_tasks.copy()
        repetitive_tasks.append(repetitive_tasks.pop(0))
        users = list(room.users.values_list('id', flat=True))
        shuffle(users)
        scope_cost = room.current_round * (user_count - 2) * 10
        for i in range(user_count):
            UserTask.objects.create(task_id=game_tasks[i], user_id=users[i], scope_cost=scope_cost)
            UserTask.objects.create(task_id=repetitive_tasks[i], user_id=users[i], scope_cost=scope_cost)
        return Response(status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False, url_path='get-task')
    @permission_classes([WorkingRoomPermission])
    def get_task(self, request):
        qr = self.get_queryset().filter(userroomtask__status=UserTask.PENDING, userroomtask__user=request.user)
        serializer = self.get_serializer(qr, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='set-answer')
    @permission_classes([WorkingRoomPermission])
    def set_answer(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # test
        tasks = self.get_queryset().filter(user__room=request.user.room, status=UserTask.COMPLETED)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='set-voite')
    @permission_classes([WorkingRoomPermission])
    def set_voite(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # test
        return Response(status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get-voites')
    @permission_classes([WorkingRoomPermission])
    def get_voites(self, request):
        pass

    @permission_classes([HostPermission])
    def destroy(self, request, *args, **kwargs):
        logout(request)  # should logout all users?
        return super().destroy(request, args, kwargs)
