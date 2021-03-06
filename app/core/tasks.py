from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from config.settings.common import EMAIL_HOST_USER, FRONTEND_URL


@shared_task
def send_user_reset_email(user_id):
    user = get_user_model().objects.get(user_id)
    subject = 'Friend Bucket Email Confirmation'
    html_message = render_to_string('confirmation_email.html', {'username': user.username})
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, EMAIL_HOST_USER, (user.email,), False, html_message=html_message)


@shared_task
def send_user_confirmation_email(user_id):
    user = get_user_model().objects.get(id=user_id)
    subject = 'Friend Bucket Email Confirmation'
    token = user.custom_token
    link = f'http://{FRONTEND_URL}/confirm_email/?token={token}'
    html_message = render_to_string('confirmation_email.html', {'username': user.username, 'link': link})
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, EMAIL_HOST_USER, (user.email,), False, html_message=html_message)


@shared_task
def send_user_reset_password_email(user_id):
    user = get_user_model().objects.get(id=user_id)
    subject = 'Friend Bucket Password Reset'
    token = user.custom_token
    link = f'http://{FRONTEND_URL}/reset_password/?token={token}'
    html_message = render_to_string('reset_password_email.html', {'username': user.username, 'link': link})
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, EMAIL_HOST_USER, (user.email,), False, html_message=html_message)


def send_delayed_message(room_group_name, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(room_group_name, {"type": "send_message", "room_group_name": room_group_name, "message": {"message": message}})
