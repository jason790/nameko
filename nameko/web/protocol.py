import json

from werkzeug.wrappers import Response

from nameko.exceptions import serialize, BadRequest
from nameko.web.exceptions import BadPayload


class JsonProtocol(object):

    def describe_response(self, result):
        headers = None
        if isinstance(result, tuple):
            if len(result) == 3:
                status, headers, payload = result
            else:
                status, payload = result
        else:
            payload = result
            status = 200
        return status, headers, payload

    def deserialize_ws_frame(self, payload):
        try:
            data = json.loads(payload)
            return (
                data['method'],
                data.get('data') or {},
                data.get('correlation_id'),
            )
        except Exception:
            raise BadPayload('Invalid JSON data')

    def serialize_result(self, payload, success=True, ws=False,
                         correlation_id=None):
        if success:
            wrapper = {'success': True, 'data': payload}
        else:
            wrapper = {'success': False, 'error': payload}
        if ws:
            wrapper['type'] = 'result'
        if ws or correlation_id is not None:
            wrapper['correlation_id'] = correlation_id
        return unicode(json.dumps(wrapper))

    def serialize_event(self, event, data):
        return unicode(json.dumps({
            'type': 'event',
            'event': event,
            'data': data,
        }))

    def load_payload(self, request):
        if request.mimetype == 'application/json':
            try:
                return json.load(request.stream)
            except Exception:
                raise BadPayload('Invalid JSON data')

    def response_from_result(self, result):
        status, headers, payload = self.describe_response(result)
        return Response(self.serialize_result(payload, True),
                        status=status, headers=headers,
                        mimetype='application/json')

    def response_from_exception(self, exc, expected_exceptions=()):
        if (
            isinstance(exc, expected_exceptions) or
            isinstance(exc, BadRequest)
        ):
            status_code = 400
        else:
            status_code = 500
        payload = serialize(exc)
        return Response(self.serialize_result(
            payload, False), status=status_code, mimetype='application/json')