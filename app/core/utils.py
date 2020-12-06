from datetime import datetime


def event_wrapper(event_type, **kwargs):
    return {'event_type': event_type, 'timestamp': datetime.now().timestamp()}.update(kwargs)


def greeting_event(users):
    return event_wrapper('greeting', users=users)


def start_event(tasks):
    return event_wrapper('start', questions=tasks)
