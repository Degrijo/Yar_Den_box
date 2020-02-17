import debug_toolbar

from django.urls import path, include
from django.contrib import admin

from rest_framework import routers

from app.core.views import WatcherRoomViewSet, SignUpView, LoginView, LogoutView


urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/', admin.site.urls),
    path('signup/', SignUpView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),  # schema_view = get_swagger_view(title='Pastebin API',url='/pastebin/')
]

router = routers.SimpleRouter()
router.register(r'watcher-room', WatcherRoomViewSet)
urlpatterns += router.urls
