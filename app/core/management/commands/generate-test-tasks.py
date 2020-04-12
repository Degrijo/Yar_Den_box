from django.core.management.base import BaseCommand
from app.core.models import Task


class Command(BaseCommand):
    help = 'Generation of test tasks'

    def add_arguments(self, parser):
        parser.add_argument('number', type=int)

    def handle(self, *args, **options):
        task_count = Task.objects.count() + 1
        for i in range(options.get('number', 1)):
            Task.objects.create(name=f'Test task №{task_count + i}')
            self.stdout.write(self.style.SUCCESS(f'Successfully creating test task №{task_count + i}'))
