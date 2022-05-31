import queue
import selectors
import wave
import struct
import glob
from threading import Thread
from uuid import uuid4


class ServerThread(Thread):
    def __init__(self, sock, addr):
        Thread.__init__(self)
        self._listening_socket = None
        self._sock = sock
        self._addr = addr
        self._selector = selectors.DefaultSelector()
        self._running = True
        self._authenticated = False
        self.authTokens = []
        self._outgoing_buffer = queue.Queue()

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._selector.register(self._sock, events, data=None)

    def kill_connection(self):
        self._running = False

    def run(self):
        print("\033[92m" + f"entered run on {self._sock.getsockname()}" + "\033[0m")
        try:
            while self._running:
                events = self._selector.select(timeout=1)
                for key, mask in events:
                    if mask & selectors.EVENT_READ:
                        self._read(key)
                    if mask & selectors.EVENT_WRITE and not self._outgoing_buffer.empty():
                        self._write(key)
                if not self._selector.get_map():
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self._selector.close()

    def _read(self, key):
        print("\033[92m" + f"entered read on {key.fileobj.getsockname()}" + "\033[0m")
        recv_data = self._sock.recv(1024).decode()
        if recv_data:
            print("received", repr(recv_data), "from connection", repr(key.fileobj.getpeername()))
            self.postMessage(recv_data)
        if not recv_data:
            print("closing connection", repr(key))
            self._selector.unregister(self._sock)
            self._sock.close()

    def _write(self, key):
        print("\033[92m" + f"entered write on {key.fileobj.getsockname()}" + "\033[0m")
        try:
            message = self._outgoing_buffer.get_nowait()
        except queue.Empty:
            message = None
        if message:
            sent = self._sock.send(message.encode())

    def postMessage(self, message):
        """Post message in outgoing buffer"""
        self._outgoing_buffer.put(message)
        self.process_response()


    def process_response(self):
        """This function is processing respones from client"""
        response = self._outgoing_buffer.get()
        if response == "/auth":
            self.authClient()
            self._outgoing_buffer.put("Token has been created, You can now se list of sound or play them!")
        if not self._authenticated:
            self._outgoing_buffer.put("You have to authenticate")
        else:
            if response == "/list":
                data = self.track_list()
                self._outgoing_buffer.put(data)
            if response == "cantine.wav":
                self.sendAudio("cantine.wav")
            if response == "imperialMarch.wav":
                self.sendAudio("imperialMarch.wav")

    def track_list(self):
        """Returns track list of tracks in main folder"""
        track_list = " "
        for filename in glob.glob("*.wav"):
            track_list = track_list + filename + " "
        return track_list

    def authClient(self):
        """Create authentication token and authenticate client"""
        rand_token = uuid4()
        self.authTokens.append(rand_token)
        self._authenticated = True

    def sendAudio(self, response):
        """Sends audio to client"""
        with wave.open(response, "rb") as track:
            chunk_size = 4096

            client_socket = self._sock
            chunk_data = track.readframes(chunk_size)

            while chunk_data:
                client_socket.sendall(struct.pack("I", len(chunk_data)) + chunk_data)

                chunk_data = track.readframes(chunk_size)
            print("sent data")
