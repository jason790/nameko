import eventlet

from kombu import Exchange, Queue
import pytest

from nameko.events import EventDispatcher, Event, EventTypeTooLong
from nameko.messaging import consume

EVENTS_TIMEOUT = 5

foobar_ex = Exchange('spammer.events', type='topic', durable=False)
foobar_queue = Queue(exchange=foobar_ex, routing_key='#', durable=False)


class SpamEvent(Event):
    type = 'spammed'


class Spammer(object):

    dispatch = EventDispatcher()

    def emit_event(self, data):
        self.dispatch(SpamEvent(data))


class SpamHandler(object):
    events = []

    #@handle_event('spammer', 'spammed', singleton_id='foo')
    @consume(queue=foobar_queue)
    def handle(self, evt):
        self.events.append(evt)


def test_emit_event_without_handlers(start_service):
    spammer = start_service(Spammer, 'spammer_nobody_listening')
    spammer.emit_event('ham and eggs')


def test_emit_event(start_service):
    spam_handler = start_service(SpamHandler, 'spamhandler')

    spammer = start_service(Spammer, 'spammer')
    spammer.emit_event('ham and eggs')

    events = spam_handler.events

    with eventlet.timeout.Timeout(EVENTS_TIMEOUT):
        while not events:
            eventlet.sleep()

    assert events == ['ham and eggs']


def test_event_type_too_long():
    class MyEvent(Event):
        type = 't' * 256

    with pytest.raises(EventTypeTooLong):
        MyEvent('spam')
