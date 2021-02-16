from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import serializers
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, UpdateModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from app.core.models import Room
from app.core.serializers import SigUpSerializer, LogInSerializer, ConnectGameSerializer, ListRoomSerializer, \
    CreateGameSerializer, MeSerializer


class AuthorizationViewSet(GenericViewSet):
    queryset = get_user_model().objects.all()
    authentication_classes = ()

    def get_serializer_class(self):
        if self.action == 'signup':
            return SigUpSerializer
        if self.action == 'login':
            return LogInSerializer
        return serializers.Serializer

    @action(methods=['POST'], detail=False, url_path='')
    def signup(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='')
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class PlayerViewSet(GenericViewSet, RetrieveModelMixin):
    queryset = get_user_model().objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('me', 'retrieve'):
            return MeSerializer
        return serializers.Serializer

    @action(methods=['GET'], detail=False, url_path='me')
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoomViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, RetrieveModelMixin):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == 'list':
            return super().get_queryset().annotate(player_count=Count('players'))
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ListRoomSerializer
        if self.action == 'create':
            return CreateGameSerializer
        if self.action == 'connect':
            return ConnectGameSerializer
        return serializers.Serializer

    @action(methods=['POST'], detail=False, url_path='connect')
    def connect(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
