from random import sample, shuffle

import requests

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Count

from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.serializers import Serializer

from app.core.models import Room, Task, UserTaskRoom
from app.core.serializers import SigUpSerializer, LogInSerializer, ConnectGameSerializer, ListRoomSerializer, \
    CreateGameSerializer, UserSerializer
from app.core.permissions import HostPermission


class AuthorizationViewSet(GenericViewSet):
    queryset = get_user_model().objects.all()
    authentication_classes = ()

    def get_serializer_class(self):
        if self.action == 'signup':
            return SigUpSerializer
        if self.action == 'login':
            return LogInSerializer

    @action(methods=['POST'], detail=False, url_path='')
    def signup(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        data = {'refresh': str(refresh), 'access': str(refresh.access_token)}
        return Response(data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='')
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = get_user_model().objects.get(username=serializer.data['username'], password=serializer.data['password'])
        except get_user_model().DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        refresh = RefreshToken.for_user(user)
        data = {'refresh': str(refresh), 'access': str(refresh.access_token)}
        return Response(data, status=status.HTTP_201_CREATED)


class PlayerViewSet(GenericViewSet):
    queryset = get_user_model().objects.none()
    permission_classes = [IsAuthenticated]
    serializer_class = ConnectGameSerializer

    @action(methods=['POST'], detail=False, url_path='connect-game')
    def connect_game(self, request, *args, **kwargs):
        room = get_object_or_404(Room, name=request.data['name'])
        if room.status != Room.PENDING:
            return Response(data='The game started yet', status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user.room = room
        user.role = user.PLAYER
        user.save()
        return Response(status=status.HTTP_201_CREATED)


class HostViewSet(GenericViewSet):
    queryset = get_user_model().objects.none()

    def get_permissions(self):
        if self.action in ['start_game', 'finish_game']:
            return [HostPermission()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create_game':
            return CreateGameSerializer
        return Serializer

    @action(methods=['POST'], detail=False, url_path='create-game')
    def create_game(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = Room.objects.create(name=serializer.validated_data['name'], max_round=serializer.validated_data['max_round'])
        user = request.user
        user.room = room
        user.role = user.HOST
        user.save()
        return Response(status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='start-game')
    def start_game(self, request):
        room = request.user.room
        user_count = room.users.count()
        if user_count < 3:
            return Response(data='Counter of user smaller than 3', status=status.HTTP_400_BAD_REQUEST)
        tasks = Task.objects.exclude(users__room__id=room.id)
        if tasks.count() < user_count:
            return Response(data='Task counter should be bigger or equal than user counter',
                            status=status.HTTP_204_NO_CONTENT)
        room.status = Room.WORKING
        room.save()
        game_tasks = sample(list(tasks.values_list('id', flat=True)), k=user_count)
        repetitive_tasks = game_tasks.copy()
        repetitive_tasks.append(repetitive_tasks.pop(0))
        users = list(room.users.values_list('id', flat=True))
        shuffle(users)
        scope_cost = room.current_round * (user_count - 2) * 10
        for i in range(user_count):
            UserTaskRoom.objects.create(task_id=game_tasks[i], user_id=users[i], scope_cost=scope_cost)
            UserTaskRoom.objects.create(task_id=repetitive_tasks[i], user_id=users[i], scope_cost=scope_cost)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['DELETE'], detail=False, url_path='finish-game')
    def finish_game(self):
        self.request.user.room.status = Room.FINISHED
        return Response(status=status.HTTP_204_NO_CONTENT)


class MenuViewSet(GenericViewSet, ListModelMixin):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated]
    SITE_URL = 'http://127.0.0.1:5000/'

    def get_serializer_class(self):
        if self.action == 'list':
            return ListRoomSerializer
        return UserSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().annotate(capacity=Count('users'))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='user-inf')
    def user_inf(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get-tasks')
    def get_tasks(self, request):
        r = requests.get(self.SITE_URL)
        return Response(r.text, status=status.HTTP_200_OK)
