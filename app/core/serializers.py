from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from app.core.constants import MAX_PLAYER_COUNT
from app.core.models import Room, Player


class SigUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = self.Meta.model(email=validated_data.get('email'),
                               username=validated_data.get('username'))
        password = validated_data.get('password')
        if password is not None:
            user.set_password(password)
        user.save()
        # user.email_user()
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class LogInSerializer(serializers.ModelSerializer):
    username_or_email = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ('username_or_email', 'password')

    def validate(self, attrs):
        value = attrs.get('username_or_email')
        users = get_user_model().objects.filter(Q(username=value) | Q(email=value)).distinct()
        if users.count() != 1:
            raise serializers.ValidationError({'username_or_email': ['No such user']})
        if not users.first().check_password(attrs.get('password')):
            raise serializers.ValidationError({'password': ['Wrong password']})
        return attrs

    def create(self, validated_data):
        value = validated_data.get('username_or_email')
        return get_user_model().objects.filter(Q(username=value) | Q(email=value)).distinct().first()  # optimize it

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class CreateRoomSerializer(serializers.ModelSerializer):
    username = serializers.CharField(allow_blank=True)

    class Meta:
        model = Room
        fields = ('username', 'name', 'max_round')

    def create(self, validated_data):
        username = validated_data.pop('username')
        room = Room.objects.create(**validated_data)
        user = self.context.get('request').user
        if not username:
            username = user.username
        Player.objects.create(user=user,
                              username=username,
                              room=room,
                              host=True,
                              color=room.random_player_color)
        return room

    def to_representation(self, instance):
        return {}


class ConnectRoomSerializer(serializers.ModelSerializer):
    username = serializers.CharField(allow_blank=True)
    name = serializers.CharField()

    class Meta:
        model = Room
        fields = ('username', 'name', 'password')

    def validate(self, attrs):
        if not Room.objects.filter(name=attrs.get('name')).exists():
            raise serializers.ValidationError({'name': ['No room with such name']})
        room = Room.objects.get(name=attrs.get('name'))
        if room.private and not room.check_password(attrs.get('password')):
            raise serializers.ValidationError({'password': ['Incorrect password']})
        if not room.is_has_user(self.context.get('request').user) and room.status != Room.PENDING:
            raise serializers.ValidationError('The game already started')
        return attrs

    def create(self, validated_data):
        user = self.context.get('request').user
        room = Room.objects.get(name=validated_data.get('name'))
        if Player.objects.filter(user=user, room=room).exists():
            return room
        username = validated_data.get('username')
        if not username:
            username = user.username
        Player.objects.create(user=user, username=username, room=room, color=room.random_player_color)
        return room

    def to_representation(self, instance):
        return {}


class RoomSerializer(serializers.ModelSerializer):
    max_player_count = serializers.ReadOnlyField(default=MAX_PLAYER_COUNT)

    class Meta:
        model = Room
        fields = ('name', 'player_count', 'max_player_count', 'current_round', 'max_round', 'status', 'private')

    def get_status(self, obj):
        return dict(Room.STATUS_TYPE).get(obj.status)


class PasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField()
    password_repeat = serializers.CharField()

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_repeat'):
            raise serializers.ValidationError("Passwords doesn't match")
        return attrs

    def create(self, validated_data):
        user = validated_data.get('user')
        user.set_password(validated_data.get('password'))
        user.save()
        return {}

    def to_representation(self, instance):
        return {'status': 'Ok'}


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username')
