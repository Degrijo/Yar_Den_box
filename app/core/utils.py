from random import sample
from string import ascii_uppercase, digits

from django.utils import timezone

from app.core.constants import PASSWORD_CHARS_NUMBER


def generate_password():
    return ''.join(sample(ascii_uppercase + digits, PASSWORD_CHARS_NUMBER))


def event_wrapper(event_type, **kwargs):
    data = {'eventType': event_type, 'timestamp': timezone.now().timestamp()}
    data.update(kwargs)
    print(data)
    return data


def connection_event():
    return event_wrapper('connection', message='connection ok')


def greeting_event(name, password, users):
    return event_wrapper('greeting', name=name, password=password, users=users)


def start_event(tasks):
    return event_wrapper('questionList', questions=tasks)


def error_event(message):
    return event_wrapper('error', message=message)


def is_alive_event():
    return event_wrapper('isAlive')


def define_event(user_id, username, is_host):
    return event_wrapper('define', userId=user_id, username=username, isHost=is_host)


def answer_accepted_event(user_id, username):
    return event_wrapper('answerAccepted', userId=user_id, username=username)


def vote_event(tasks):
    return event_wrapper('voteList', tasks=tasks)


def winner_event(username):
    return event_wrapper('winner', username=username)


def timeout_event():
    return event_wrapper('timeout')


def reconnect_event(event):
    return event_wrapper('reconnect', inner=event)


def score_event(scores):
    return event_wrapper('score', scores=scores)


def pause_event():
    return event_wrapper('pause')


def resume_event():
    return event_wrapper('resume')


def group_by(items, group_name, *args):
    result = {}
    for item in items:
        keys = ([item.pop(key) for key in args])
        result.setdefault(tuple(keys), []).append(item)
    grouped = []
    for key, value in result.items():
        data = dict(zip(args, key))
        data.setdefault(group_name, value)
        grouped.append(data)
    return grouped
