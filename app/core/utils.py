from random import sample
from string import ascii_uppercase, digits

import jsonschema
from django.utils import timezone
from jsonschema import validate

from app.core.constants import PASSWORD_CHARS_NUMBER, ANSWERING_DURATION
from app.core.schemas import EVENTS_SCHEMAS


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


def start_event(questions):
    return event_wrapper('questionList', questions=questions, timeForAnswer=ANSWERING_DURATION)


def error_event(message):
    return event_wrapper('error', message=message)


def is_alive_event():
    return event_wrapper('isAlive')


def define_event(user_id, username, is_host):
    return event_wrapper('define', userId=user_id, username=username, isHost=is_host)


def answer_accepted_event(players):
    return event_wrapper('answerAccepted', players=players)


def vote_event(tasks):
    return event_wrapper('voteList', tasks=tasks, )


def winner_event(username):
    return event_wrapper('winner', username=username)


def reconnect_event(event):
    return event_wrapper('reconnect', inner=event)


def score_event(scores):
    return event_wrapper('score', scores=scores)


def pause_event():
    return event_wrapper('pause')


def resume_event():
    return event_wrapper('resume')


def validate_schema(data, schema):
    try:
        validate(data, schema)
    except jsonschema.exceptions.ValidationError:
        return False
    return True


def validate_event(event):
    return any([validate_schema(event, schema) for schema in EVENTS_SCHEMAS])


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


def simple_group(items, grouped_field):
    result = {}
    for item in items:
        result.setdefault(item.pop(grouped_field), []).append(item)
    return result.items()
