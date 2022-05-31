import NodeServerThread
import socket
import selectors
from threading import Thread


class Server(Thread):
    def __init__(self, host="127.0.0.1", port=12345, connected=None):
        Thread.__init__(self)
        # Network components
        self._host = host
        self._port = port
        self.connected = connected
        self._listening_socket = None
        self._selector = selectors.DefaultSelector()

        self._modules = []

    def _configureServer(self):
        self._listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listening_socket.bind((self._host, self._port))
        self._listening_socket.listen()

        print("listening on", (self._host, self._port))
        self._listening_socket.setblocking(False)
        self._selector.register(self._listening_socket, selectors.EVENT_READ, data=None)

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()
        print("accepted connection from", addr)

        conn.setblocking(False)
        module = NodeServerThread.ServerThread(conn, addr)
        self._modules.append(module)
        module.start()

    def run(self):
        self._configureServer()

        try:
            while True:
                events = self._selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        pass
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self._selector.close()