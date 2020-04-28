from datetime import datetime

from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model

from config.settings.common import AuthTokenValidTime

from app.core.models import Room


class AuthTokenPermission(BasePermission):
    message = 'Auth token is not valid'

    def has_permission(self, request, view):
        if not request.data.get('token'):
            return False
        try:
            user = get_user_model().objects.get(auth_token__key=request.data.get('token'))
            if (datetime.now() - user.auth_token.created.replace(tzinfo=None)).days < AuthTokenValidTime:
                request.user = user
                return True
            return False
        except get_user_model().DoesNotExist:
            return False


class PlayerPermission(AuthTokenPermission):
    message = "For access this view user's role should be Player"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == get_user_model().PLAYER


class HostPermission(AuthTokenPermission):
    message = "For access this view user's role should be Host"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == get_user_model().HOST


class WorkingRoomPermission(AuthTokenPermission):
    message = "For access this view room's status should be Working"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.room and request.user.room.status == Room.WORKING


class PendingRoomPermission(AuthTokenPermission):
    message = "For access this view room's status should be Pending"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.room and request.user.room.status == Room.PENDING
