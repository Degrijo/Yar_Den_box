from string import ascii_uppercase, digits
from random import choices, sample, shuffle

from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import get_object_or_404
from django.db.models import Count

from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from app.core.models import Room, Task, UserTaskRoom
from app.core.serializers import SigUpSerializer, LogInSerializer, HostRoomSerializer, ConnectGameSerializer, \
    TaskSerializer, AnswerSerializer, VoitingSerializer, RoomSerializer, TokenSerializer
from app.core.permissions import AuthTokenPermission, HostPermission, PlayerPermission, WorkingRoomPermission, \
    PendingRoomPermission


class AuthorizationViewSet(GenericViewSet):
    queryset = get_user_model().objects.all()

    def get_permissions(self):
        if self.action == 'logout':
            return [AuthTokenPermission()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'signup':
            return SigUpSerializer
        if self.action == 'login':
            return LogInSerializer
        return TokenSerializer

    @action(methods=['POST'], detail=False, url_path='')
    def signup(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='')
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, username=serializer.data['username'], password=serializer.data['password'])
        if user:
            token = Token.objects.get_or_create(user=user)
            token.update(key=token.generate_key())
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='')
    def logout(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlayerViewSet(GenericViewSet):
    queryset = get_user_model().objects.none()
    permission_classes = [AuthTokenPermission]
    serializer_class = ConnectGameSerializer

    @action(methods=['POST'], detail=False, url_path='connect-game')
    def connect_game(self, request, *args, **kwargs):
        room = get_object_or_404(Room, address=request.data['address'])
        if room.status != Room.PENDING:
            return Response(data='The game started yet', status=status.HTTP_400_BAD_REQUEST)
        get_user_model().objects.create(username=request.data['username'], room=room, role=get_user_model().PLAYER)
        return Response(status=status.HTTP_201_CREATED)


class HostViewSet(GenericViewSet):
    queryset = get_user_model().objects.none()

    def get_permissions(self):
        if self.action in ['start_game', 'finish_game']:
            return [HostPermission()]
        return [AuthTokenPermission()]

    def get_serializer_class(self):
        return HostRoomSerializer

    @action(methods=['POST'], detail=False, url_path='create-game')
    def create_game(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        while True:
            address = ''.join(choices(ascii_uppercase + digits, k=Room._meta.get_field('address').max_length))
            if not Room.objects.filter(address=address).exists():
                break
        room = Room.objects.create(address=address, max_round=request.data['max_round'])
        user = request.user
        user.room = room
        user.role = user.HOST
        user.save()
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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


class GameViewSet(GenericViewSet, ListModelMixin):
    permission_classes = [WorkingRoomPermission]

    def get_queryset(self):
        if self.action == 'join-room':
            return get_user_model().objects.all()
        elif self.action == 'set-answer':
            return UserTaskRoom.objects.all()
        return Room.objects.filter(status=Room.PENDING)

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'get_tasks':
            return TaskSerializer
        elif self.action == 'set_answer':
            return AnswerSerializer
        elif self.action == 'set_voite':
            return VoitingSerializer
        elif self.action == 'list':
            return RoomSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().annotate(capacity=Count('users'))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='get-tasks')
    def get_tasks(self, request):
        qr = self.get_queryset().filter(userroomtask__status=UserTaskRoom.PENDING, userroomtask__user=request.user)
        serializer = self.get_serializer(qr, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='set-answer')
    def set_answer(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get-answers')
    def get_answers(self, request):
        return self.get_queryset().filter(user__room=request.user.room, status=UserTaskRoom.COMPLETED)

    @action(methods=['POST'], detail=False, url_path='set-voite')
    def set_voite(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # test
        return Response(status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get-voites')
    def get_voites(self, request):
        pass
