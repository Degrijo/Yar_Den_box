from django.core.management.base import BaseCommand
from app.core.models import GeneralVariable


class Command(BaseCommand):
    help = 'Initialization of general variables'

    def handle(self, *args, **options):
        for obj in ["Users counter", "Rooms counter", "Own tasks counter"]:
            GeneralVariable.objects.create(name=obj, value=0)
            self.stdout.write(self.style.SUCCESS(f'Successfully creating variable {obj}'))
