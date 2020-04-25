from rest_framework.permissions import IsAuthenticated, BasePermission
from django.contrib.auth import get_user_model

from app.core.models import Room


class PlayerPermission(IsAuthenticated):
    message = "For access this view user's role should be Player"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == get_user_model().PLAYER


class HostPermission(IsAuthenticated):
    message = "For access this view user's role should be Host"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == get_user_model().HOST


class WorkingRoomPermission(IsAuthenticated):
    message = "For access this view room's status should be Working"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.room and request.user.room.status == Room.WORKING


class PendingRoomPermission(IsAuthenticated):
    message = "For access this view room's status should be Pending"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.room and request.user.room.status == Room.PENDING
