import debug_toolbar
from django.urls import path, include
from django.contrib import admin
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView

from app.core.drf_views import AuthorizationViewSet, PlayerViewSet, RoomViewSet


urlpatterns = [
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/', admin.site.urls),
]

router = routers.SimpleRouter()
router.register(r'auth', AuthorizationViewSet, basename='auth')
router.register(r'player', PlayerViewSet, basename='player')
router.register(r'room', RoomViewSet, basename='room')
urlpatterns += router.urls
