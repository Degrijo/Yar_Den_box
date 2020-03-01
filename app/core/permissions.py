from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from app.core.models import Room


class PlayerPermission(IsAuthenticated):
    message = "For access this view user's role should be Player"

    def has_permission(self, request, view):
        if request.user.role == get_user_model().PLAYER:
            return True
        return False


class HostPermission(IsAuthenticated):
    message = "For access this view user's role should be Host"

    def has_permission(self, request, view):
        if request.user.role == get_user_model().HOST:
            return True
        return False


class WorkingRoomPermission(IsAuthenticated):
    message = "For access this view room's status should be Working"

    def has_permission(self, request, view):
        if request.user.room.status == Room.WORKING:
            return True
        return False


class PendingRoomPermission(IsAuthenticated):
    message = "For access this view room's status should be Pending"

    def has_permission(self, request, view):
        if request.user.room.status == Room.PENDING:
            return True
        return False
