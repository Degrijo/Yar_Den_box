import debug_toolbar

from django.urls import path, include
from django.contrib import admin

from rest_framework import routers

from app.core.views import RoomViewSet


urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/', admin.site.urls),
]

router = routers.SimpleRouter()
router.register(r'rooms', RoomViewSet, basename='rooms')
urlpatterns += router.urls
