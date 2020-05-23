from django.core.management.base import BaseCommand
from app.core.models import Task

import requests


class Command(BaseCommand):
    help = 'get tasks from nn'
    SITE_URL = 'http://127.0.0.1:5000/'

    def handle(self, *args, **options):
        r = requests.get(self.SITE_URL)
        print(r.text)
