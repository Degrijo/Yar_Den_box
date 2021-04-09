from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError

from app.core.constants import MAX_PLAYER_COUNT
from app.core.models import Room, Player, CustomToken


class SigUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')

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
        self.instance = users.first()
        if not self.instance.check_password(attrs.get('password')):
            raise serializers.ValidationError({'password': ['Wrong password']})
        # if not self.instance.is_confirmed:  # TODO turn on for prod
        #     raise serializers.ValidationError("User isn't confirmed")
        return attrs

    def update(self, instance, validated_data):
        instance.login_fill()
        return instance

    def to_representation(self, instance):
        return instance.tokens_pair


class ResendConfirmEmailSerializer(serializers.ModelSerializer):
    username_or_email = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ('username_or_email', 'password')

    def validate(self, attrs):
        users = self.Meta.model.objects.get_user(attrs.get('username_or_email'))
        if users.count() != 1:
            raise serializers.ValidationError({'username_or_email': ['No such user']})
        self.instance = users.first()
        if not self.instance.check_password(attrs.get('password')):
            raise serializers.ValidationError({'password': ['Wrong password']})
        if self.instance.is_confirmed:
            raise serializers.ValidationError("User is confirmed")
        return attrs

    def update(self, instance, validated_data):
        instance.send_confirmation()
        return instance

    def to_representation(self, instance):
        return {}


class ConfirmEmailSerializer(serializers.Serializer):
    confirm_token = serializers.CharField()

    def validate_confirm_token(self, value):
        try:
            token = CustomToken(token=value, verify=False)
            self.instance = get_user_model().objects.get(id=token.payload.get('user_id'))
        except (TokenError or get_user_model().DoesNotExist):
            raise serializers.ValidationError("Token isn't valid")
        return value

    def update(self, instance, validated_data):
        instance.is_confirmed = True
        instance.save(update_fields=('is_confirmed',))
        return instance

    def to_representation(self, instance):
        return instance.tokens_pair


class SendRestorePasswordSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()

    def validate_username_or_email(self, value):
        users = get_user_model().objects.get_user(value)
        if users.count() != 1:
            raise serializers.ValidationError('No such user')
        self.instance = users.first()

    def update(self, instance, validated_data):
        instance.send_reset_password()
        return instance

    def to_representation(self, instance):
        return {}


class ResetPasswordSerializer(serializers.ModelSerializer):
    reset_token = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ('reset_token', 'password')

    def validate_reset_token(self, value):
        try:
            token = CustomToken(token=value, verify=False)
            self.instance = get_user_model().objects.get(id=token.payload.get('user_id'))
        except (TokenError or get_user_model().DoesNotExist):
            raise serializers.ValidationError("Token isn't valid")
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data.get('password'))
        instance.save(update_fields=('password',))
        return instance

    def to_representation(self, instance):
        return instance.tokens_pair


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
        data = {'name': instance.name}
        if instance.private:
            data['password'] = instance.password
        return data


class ConnectRoomSerializer(serializers.ModelSerializer):
    username = serializers.CharField(allow_blank=True)
    name = serializers.CharField()

    class Meta:
        model = Room
        fields = ('username', 'name', 'password')

    def validate(self, attrs):
        try:
            self.instance = self.Meta.model.objects.get(name=attrs.get('name'))
        except self.Meta.model.DoesNotExist:
            raise serializers.ValidationError({'name': 'No room with such name'})
        if self.instance.private and not self.instance.check_password(attrs.get('password')):
            raise serializers.ValidationError({'password': ['Incorrect password']})
        if not self.instance.is_has_user(self.context.get('request').user) and self.instance.status != Room.PENDING:
            raise serializers.ValidationError('The game already started')
        return attrs

    def update(self, instance, validated_data):
        user = self.context.get('request').user
        if not Player.objects.filter(user=user, room=instance).exists():
            Player.objects.create_player(user, instance, validated_data.get('username'))
        return instance

    def to_representation(self, instance):
        data = {'name': instance.name, 'players': instance.players.values_list('username', flat=True)}
        if instance.private:
            data['password'] = instance.password
        return data


class RoomSerializer(serializers.ModelSerializer):
    max_player_count = serializers.ReadOnlyField(default=MAX_PLAYER_COUNT)

    class Meta:
        model = Room
        fields = ('name', 'player_count', 'max_player_count', 'current_round', 'max_round', 'status', 'private')

    def get_status(self, obj):
        return dict(Room.STATUS_TYPE).get(obj.status)


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username')
