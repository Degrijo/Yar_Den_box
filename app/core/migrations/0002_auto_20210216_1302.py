# Generated by Django 3.0.6 on 2021-02-16 13:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='player',
            unique_together={('username', 'room')},
        ),
    ]
