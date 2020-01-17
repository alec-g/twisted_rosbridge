import json
import logging

from rossock.managers.rossock_core import Message

class RosBridgeException(Exception):
    """Exception raised on the ROS bridge communication."""
    pass

class RosBridgeProtocol(object):
    """Implements the websocket client protocol to encode/decode JSON ROS Bridge messages."""

    def __init__(self, *args, **kwargs):
        super(RosBridgeProtocol, self).__init__(*args, **kwargs)
        self.factory = None
        self._pending_service_requests = {}
        self._message_handlers = {
            'publish': self._handle_publish,
        }

    def on_message(self, payload):
        message = Message(json.loads(payload.decode('utf8')))
        handler = self._message_handlers.get(message['op'], None)
        if not handler:
            raise RosBridgeException(
                'No handler registered for operation "%s"' % message['op'])

        handler(message)

    def send_ros_message(self, message):
        """Encode and serialize ROS Bridge protocol message.
        Args:
            message (:class:`.Message`): ROS Bridge Message to send.
        """
        try:
            json_message = json.dumps(dict(message)).encode('utf8')
            self.send_message(json_message)
        except Exception as exception:
            # TODO: Check if it makes sense to raise exception again here
            # Since this is wrapped in many layers of indirection
            pass

    def register_message_handlers(self, operation, handler):
        """Register a message handler for a specific operation type.
        Args:
            operation (:obj:`str`): ROS Bridge operation.
            handler: Callback to handle the message.
        """
        if operation in self._message_handlers:
            raise RosBridgeException(
                'Only one handler can be registered per operation')

        self._message_handlers[operation] = handler

    def _handle_publish(self, message):
        self.factory.emit(message['topic'], message['msg'])
