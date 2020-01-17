import threading

from rossock.comms.protocol import RosBridgeProtocol
from rossock.managers.event_emitter import EventEmitterMixin
from rossock import misc

from twisted.internet import reactor
from twisted.internet.error import ConnectionDone
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

class TCPClientProtocol(RosBridgeProtocol, Protocol):
    def __init__(self, *args, **kwargs):
        super(TCPClientProtocol, self).__init__(*args, **kwargs)

    def connectionMade(self):
        misc.formatted_print('RosBridgeTCPComms\t|\tConnection made', None, 'success')
        misc.formatted_print('RosBridgeTCPComms\t|\tFactory is ready!',None,'success')
        self.factory.connected = True
        self.factory.ready(self)

    def dataReceived(self, data):
        self.on_message(data)

    def connectionLost(self, reason):
        misc.formatted_print('RosBridgeTCPComms\t|\tConnection lost', None, 'error')

    def dataSend(self, data):
        misc.formatted_print('RosBridgeTCPComms\t|\t Sending data')
        self.transport.write(data)

class TCPClientFactory(EventEmitterMixin, ReconnectingClientFactory):
    """Factory to create instances of the ROS Bridge protocol built on top of Twisted."""
    protocol = TCPClientProtocol

    def __init__(self, host, port, *args, **kwargs):
        super(TCPClientFactory, self).__init__(*args, **kwargs)
        self._host = host
        self._port = port
        self._proto = None
        self._manager = None
        self.connected = False

    def connect(self):
        misc.formatted_print('TCP: ' + str(self._host) + ':' + str(self._port) + '\t|\tConnecting..', None, 'connecting')
        reactor.connectTCP(self._host, self._port, self)

    @property
    def is_connected(self):
        """Indicate if the TCP connection is open or not.
        Returns:
            bool: True if TCP is connected, False otherwise.
        """
        return self.connected

    def on_ready(self, callback):
        if self._proto:
            callback(self._proto)
        else:
            self.once('ready', callback)

    def ready(self, proto):
        self._proto = proto
        self.emit('ready', proto)

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
            misc.formatted_print('RosBridgeTCPComms\t|\tTwisted reactor is already running', None, 'error')
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
