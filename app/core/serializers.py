from django.db.models import Sum
from django.contrib.auth import get_user_model

from rest_framework.serializers import ModelSerializer, SerializerMethodField

from app.core.models import Room, Task


class SignUpSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            'username',
            'password',
            'role',
        )
        write_only_fields = (
            'password',
        )


class LoginSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            'username',
            'password',
        )
        write_only_fields = (
            'password',
        )


class RoomSerializer(ModelSerializer):
    class Meta:
        model = Room
        fields = (
            'address',
            'watchers_number',
        )
        read_only_fields = (
            'address',
            'watchers_number',
        )


class DetailRoomSerializer(RoomSerializer):  # check with select and without
    watchers_top_number = SerializerMethodField(read_only=True)
    total_sum_price = SerializerMethodField(read_only=True)
    current_task = SerializerMethodField(read_only=True)

    class Meta(RoomSerializer):
        model = Room
        fields = (
            'address',
            'watchers_number',
            'watchers_top_number',
            'total_sum_prize',
            'current_task',
        )

    def get_watchers_top_number(self, obj):
        return

    def get_total_sum_price(self, obj):
        qs = Task.objects.filter(room=obj).aggregate(Sum('prize'))
        return qs.prize__sum

    def get_current_task(self, obj):
        if Task.objects.filter(room=obj, status=Task.APPROVED_STATUS).count() == 1:
            return Task.objects.get(room=obj, status=Task.APPROVED_STATUS).name
        return ""
