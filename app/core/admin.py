from django.contrib import admin
from django.contrib.auth import get_user_model

from app.core.models import Room, Task, Player, PlayerTask, Color

admin.site.site_header = 'YarDenBox Administration'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')

    def status(self, obj):
        return dict(Room.STATUS_TYPE).get(obj.status)


admin.site.register(Task)
admin.site.register(get_user_model())
admin.site.register(Player)
admin.site.register(PlayerTask)
admin.site.register(Color)
