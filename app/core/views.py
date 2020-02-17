from string import ascii_uppercase, digits
from random import choices

from django.db.models import Count
from django.contrib.auth import login, logout, authenticate, get_user_model

from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status

from app.core.models import Room, Task
from app.core.serializers import SignUpSerializer, LoginSerializer, RoomSerializer
from app.core.permissions import PlayerPermission, WatcherPermission


class SignUpView(CreateAPIView):
    queryset = get_user_model()
    serializer_class = SignUpSerializer

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if data['role'] == get_user_model().PLAYER:
            while True:
                address = ''.join(choices(ascii_uppercase + digits, k=Room.address.max_length))
                if not Room.objects.filter(address=address).exists():
                    break
            room = Room.objects.create(address=address)
            data['players_room'] = room.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = authenticate(request, username=data['username'], password=data['password'])
        print(user)
        if user:
            login(request, user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class LoginView(CreateAPIView):
    queryset = get_user_model()
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        user = authenticate(request, username=request.data['username'], password=request.data['password'])
        if user:
            login(request, user)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class LogoutView(DestroyAPIView):
    def delete(self, request, *args, **kwargs):
        logout(request)
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class WatcherRoomViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = (IsAuthenticated, WatcherPermission)

    def get_queryset(self):  # add select and prefetch related
        return self.queryset.annotate(watchers_number=Count('watchers')).order_by('-watchers_number')

    @action(detail=True, methods=['GET'], url_path='favorite-rooms')
    def favorite_rooms(self, request):
        queryset = self.get_queryset().filter(userroom__favorite=True, users__id=request.user.id).values_list('room__id', 'room__player__username', 'watchers_number')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='previous-rooms')
    def previous_rooms(self, request):
        queryset = self.get_queryset().filter(users__id=request.user.id).values_list('room__id', 'room__player__username', 'watchers_number')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().values_list('room__id', 'room__player__username', 'watchers_number')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# class PlayerRoomViewSet(GenericViewSet):  # таски пользователей, количество пользователей, место среди комнат

