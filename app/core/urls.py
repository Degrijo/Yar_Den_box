import debug_toolbar

from django.urls import path, include
from django.contrib import admin

from rest_framework import routers

from rest_framework_simplejwt.views import TokenRefreshView

from app.core.drf_views import AuthorizationViewSet, PlayerViewSet, HostViewSet, MenuViewSet
from app.core.django_views import statistic, home, algorithm, links, realization
from app.core.swagger_views import get_swagger_view

schema_view = get_swagger_view(title='Yar Den Box API')


urlpatterns = [
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/', admin.site.urls),
    path('statistic/', statistic),
    path('', home),
    path('algorithm/', algorithm),
    path('links/', links),
    path('realization/', realization),
]

router = routers.SimpleRouter()
router.register(r'auth', AuthorizationViewSet, basename='auth')
router.register(r'host', HostViewSet, basename='host')
router.register(r'player', PlayerViewSet, basename='player')
router.register(r'menu', MenuViewSet, basename='menu')
urlpatterns += router.urls
