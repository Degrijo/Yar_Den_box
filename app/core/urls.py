import debug_toolbar

from django.urls import path, include

from rest_framework import routers

from app.core.views import home, StartView, PlayerViewSet, HostViewSet, GameViewSet


urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('statistic/', home),
    path('', StartView.as_view()),
]

router = routers.SimpleRouter()
router.register(r'host', HostViewSet, basename='host')
router.register(r'player', PlayerViewSet, basename='player')
router.register(r'game', GameViewSet, basename='game')
urlpatterns += router.urls
