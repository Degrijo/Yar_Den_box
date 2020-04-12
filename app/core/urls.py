import debug_toolbar

from django.urls import path, include
from django.contrib import admin

from rest_framework import routers

from app.core.views import home, GameViewSet


urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/', admin.site.urls),
    path('statistic/', home)
]

router = routers.SimpleRouter()
router.register(r'game', GameViewSet, basename='game')
urlpatterns += router.urls
