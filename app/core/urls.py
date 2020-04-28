import debug_toolbar

from django.urls import path, include

from rest_framework import routers

from app.core.drf_views import AuthorizationViewSet, PlayerViewSet, HostViewSet, GameViewSet
from app.core.swagger_views import get_swagger_view

schema_view = get_swagger_view(title='Yar Den Box API')


urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    # path('statistic/', home),
    path('', schema_view),
]

router = routers.SimpleRouter()
router.register(r'auth', AuthorizationViewSet, basename='auth')
router.register(r'host', HostViewSet, basename='host')
router.register(r'player', PlayerViewSet, basename='player')
router.register(r'game', GameViewSet, basename='game')
urlpatterns += router.urls
