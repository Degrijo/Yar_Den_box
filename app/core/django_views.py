from django.shortcuts import render
from django.contrib.auth import get_user_model

from app.core.models import Room, Task


def statistic(request):
    data = {
        'Общее количество пользователей': get_user_model().objects.count(),
        'Общее количество комнат': Room.objects.count(),
        'Общее количество заданий': Task.objects.count(),
        'Количество игроков онлайн': get_user_model().objects.filter(role__in=[get_user_model().HOST, get_user_model().PLAYER]).count(),
        'Количество комнат онлайн': Room.objects.filter(status=Room.WORKING).count()
    }
    return render(request, 'statistic.html', context={'data': data})


def home(request):
    return render(request, 'home.html')


def algorithm(request):
    return render(request, 'algo.html')


def links(request):
    return render(request, 'links.html')


def realization(request):
    return render(request, 'realization.html')
