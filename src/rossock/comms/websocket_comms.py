import threading
import websocket

from autobahn.twisted.websocket import WebSocketClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol
from autobahn.twisted.websocket import connectWS
from autobahn.websocket.util import create_url

from rossock.comms.protocol import RosBridgeProtocol
from rossock.managers.event_emitter import EventEmitterMixin
from rossock import misc

from twisted.internet import reactor
from twisted.internet.error import ConnectionDone
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

class WebSocketClientProtocol(RosBridgeProtocol, WebSocketClientProtocol):
    def __init__(self, *args, **kwargs):
        super(WebSocketClientProtocol, self).__init__(*args, **kwargs)

    def onConnect(self, response):
        pass

    def onOpen(self):
        misc.formatted_print('RosBridgeWebSock\t|\tConnection made', None, 'success')
        misc.formatted_print('RosBridgeWebSock\t|\tFactory is ready!',None,'success')
        self.factory.ready(self)

    def onMessage(self, payload, isBinary):
        if isBinary:
            raise NotImplementedError('Add support for binary messages')

        try:
            self.on_message(payload)
        except Exception:
            pass

    def onClose(self, wasClean, code, reason):
        misc.formatted_print('RosBridgeWebSock\t|\tClosing socket.',None,'error')

    def send_message(self, payload):
        return self.sendMessage(payload, isBinary=False, fragmentSize=None, sync=False, doNotCompress=False)

    def send_close(self):
        self.sendClose()


class WebSocketClientFactory(EventEmitterMixin, ReconnectingClientFactory, WebSocketClientFactory):
    """Factory to create instances of the ROS Bridge protocol built on top of Twisted."""
    protocol = WebSocketClientProtocol

    def __init__(self, *args, **kwargs):
        super(WebSocketClientFactory, self).__init__(*args, **kwargs)
        self._proto = None
        self._manager = None
        self.setProtocolOptions(closeHandshakeTimeout=5)

    def connect(self):
        """Establish WebSocket connection to the ROS server defined for this factory."""
        self.connector = connectWS(self)

    @property
    def is_connected(self):
        """Indicate if the WebSocket connection is open or not.
        Returns:
            bool: True if WebSocket is connected, False otherwise.
        """
        return self.connector and self.connector.state == 'connected'

    def on_ready(self, callback):
        if self._proto:
            callback(self._proto)
        else:
            self.once('ready', callback)

    def ready(self, proto):
        self._proto = proto
        self.emit('ready', proto)

    def startedConnecting(self, connector):
        pass

    def clientConnectionLost(self, connector, reason):
        self.emit('close', self._proto)

        # Do not try to reconnect if the connection was closed cleanl
        if reason.type is not ConnectionDone:
            ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

        self._proto = None

    def clientConnectionFailed(self, connector, reason):
        ReconnectingClientFactory.clientConnectionFailed(
            self, connector, reason)
        self._proto = None

    @property
    def manager(self):
        """Get an instance of the event loop manager for this factory."""
        if not self._manager:
            self._manager = TwistedEventLoopManager()

        return self._manager

    @classmethod
    def create_url(cls, host, port=None, is_secure=False):
        url = host if port is None else create_url(host, port, is_secure)
        return url


class TwistedEventLoopManager(object):
    """Manage the main event loop using Twisted reactor.
    """
    def __init__(self):
        pass

    def run(self):
        """Kick-starts a non-blocking event loop.
        This implementation starts the Twisted Reactor
        on a separate thread to avoid blocking."""

        if reactor.running:
            misc.formatted_print('RosBridgeWebSockComms\t|\tTwisted reactor is already running', None, 'error')
            return

        self._thread = threading.Thread(target=reactor.run, args=(False,))
        self._thread.daemon = True
        self._thread.start()

    def run_forever(self):
        """Kick-starts the main event loop of the ROS client.
        This implementation relies on Twisted Reactors
        to control the event loop."""
        reactor.run()

    def call_later(self, delay, callback):
        """Call the given function after a certain period of time has passed.
        Args:
            delay (:obj:`int`): Number of seconds to wait before invoking the callback.
            callback (:obj:`callable`): Callable function to be invoked when the delay has elapsed.
        """
        reactor.callLater(delay, callback)

    def call_in_thread(self, callback):
        """Call the given function on a thread.
        Args:
            callback (:obj:`callable`): Callable function to be invoked in a thread.
        """
        reactor.callInThread(callback)

    def terminate(self):
        """Signals the termination of the main event loop."""
        if reactor.running:
            reactor.stop()
