"""
WSGI config for temp_proj project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from channels.layers import get_channel_layer


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.common')

application = get_wsgi_application()
channel_layer = get_channel_layer()
