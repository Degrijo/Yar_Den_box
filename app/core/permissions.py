from rest_framework import permissions
from django.contrib.auth import get_user_model


class PlayerPermission(permissions.BasePermission):
    message = "For access this view user's role should be Player"

    def has_permission(self, request, view):
        if request.user.role == get_user_model().PLAYER:
            return True
        return False


class WatcherPermission(permissions.BasePermission):
    message = "For access this view user's role should be Watcher"

    def has_permission(self, request, view):
        if request.user.role == get_user_model().WATCHER:
            return True
        return False
