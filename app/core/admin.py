from django.contrib import admin
from django.contrib.auth import get_user_model

from app.core.models import Room, Task, Player, UserTaskRoom

admin.site.site_header = 'YarDenBox Administration'


admin.site.register(Room)
admin.site.register(Task)
admin.site.register(get_user_model())
admin.site.register(Player)
admin.site.register(UserTaskRoom)
