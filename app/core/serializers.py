from django.contrib.auth import get_user_model
from rest_framework import serializers

from app.core.constants import MAX_PLAYER_COUNT
from app.core.models import Room, Player

# check email case sensitive


class SigUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')

    def validate_username(self, value):
        if self.Meta.model.objects.list_actual_users().filter(username=value).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return value

    def validate_email(self, value):
        if self.Meta.model.objects.list_actual_users().filter(email=value).exists():
            raise serializers.ValidationError('A user with that email already exists.')
        return value

    def create(self, validated_data):
        return self.Meta.model.objects.create_user(**validated_data)

    def to_representation(self, instance):
        return {}


class LogInSerializer(serializers.ModelSerializer):
    username_or_email = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ('username_or_email', 'password')

    def validate(self, attrs):
        users = self.Meta.model.objects.get_user(attrs.get('username_or_email'))
        if users.count() != 1:
            raise serializers.ValidationError({'username_or_email': ['No such user']})
        user = users.first()
        if not user.check_password(attrs.get('password')):
            raise serializers.ValidationError({'password': ['Wrong password']})
        if not user.is_confirmed:
            raise serializers.ValidationError("User isn't confirmed")
        return attrs

    def create(self, validated_data):
        return self.Meta.model.objects.get_user(validated_data.get('username_or_email')).first()

    def to_representation(self, instance):
        return instance.tokens_pair


# class ConfirmEmailSerializer(serializers.Serializer):
#     confirm_token = serializers.CharField()
#
#     def validate(self, attrs):
#
#
#     def create(self, validated_data):
#         user =
#         user.is_confirmed = True
#         user.save(update_fields=('is_confirmed',))
#         return user
#
#     def to_representation(self, instance):
#         return instance.tokens_pair


class CreateRoomSerializer(serializers.ModelSerializer):
    username = serializers.CharField(allow_blank=True)

    class Meta:
        model = Room
        fields = ('username', 'name', 'max_round')

    def validate_name(self, value):
        if self.Meta.model.objects.list_actual_rooms().filter(name=value).exists():
            raise serializers.ValidationError('A room with that name already exists.')
        return value

    def create(self, validated_data):
        username = validated_data.pop('username')
        room = self.Meta.model.objects.create(**validated_data)
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

    def validate_name(self, value):
        if not self.Meta.model.objects.filter(name=value).exists():
            raise serializers.ValidationError('No room with such name')
        return value

    def validate(self, attrs):
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


# class PasswordResetSerializer(serializers.Serializer):
#     password = serializers.CharField()
#
#     def create(self, validated_data):
#         user = validated_data.get('user')
#         user.set_password(validated_data.get('password'))
#         user.save(update_fields=('password',))
#         return {}

    def to_representation(self, instance):
        return {}


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username')
