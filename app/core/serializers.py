from django.contrib.auth import get_user_model

from rest_framework import serializers

from app.core.models import Room


class SigUpSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')


class LogInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128)

    class Meta:
        fields = ('username', 'password')


class CreateGameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = ('name', 'max_round')


class ConnectGameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = ('name',)


class ListRoomSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(min_value=0)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ('name', 'capacity', 'current_round', 'max_round', 'status')

    def get_status(self, obj):
        return dict(obj.STATUS_TYPE).get(obj.status)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'score', 'role')

    def get_role(self, obj):
        return dict(obj.ROLE_TYPES).get(obj.role)
