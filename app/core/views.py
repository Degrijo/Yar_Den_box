from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import serializers
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from app.core.models import Room
from app.core.serializers import SigUpSerializer, LogInSerializer, ConnectRoomSerializer, RoomSerializer, \
    CreateRoomSerializer, MeSerializer


class AuthorizationViewSet(GenericViewSet):
    queryset = get_user_model().objects.all()
    authentication_classes = ()

    def get_serializer_class(self):
        if self.action == 'signup':
            return SigUpSerializer
        if self.action == 'login':
            return LogInSerializer
        if self.action == 'confirm_email':
            return
        return serializers.Serializer

    @action(methods=['POST'], detail=False)
    def signup(self, request, *args, **kwargs):
        """
        Signup
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False)
    def login(self, request, *args, **kwargs):
        """
        Login
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True)
    def confirm_email(self, request, *args, **kwargs):
        """
        Confirm Email
        """
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

    @action(methods=['GET'], detail=False)
    def me(self, request, *args, **kwargs):
        """
        Current user inf
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoomViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, RetrieveModelMixin):
    queryset = Room.objects.exclude(status=Room.FINISHED)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == 'list':
            return super().get_queryset().annotate(player_count=Count('players'))
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RoomSerializer
        if self.action == 'create':
            return CreateRoomSerializer
        if self.action == 'connect':
            return ConnectRoomSerializer
        return serializers.Serializer

    @action(methods=['POST'], detail=False)
    def connect(self, request, *args, **kwargs):
        """
        Connecting user to game room
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
