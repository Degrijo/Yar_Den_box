from django.contrib import admin

from app.core.models import Room, Task


admin.site.site_header = 'YarDenBox Administration'


admin.site.register(Room)
admin.site.register(Task)
