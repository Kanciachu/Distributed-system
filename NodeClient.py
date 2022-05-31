from threading import Thread
import selectors
import queue
import socket
import struct
import pyaudio


class NodeClient (Thread):
    def __init__(self, name, host="127.0.0.1", port=12356):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.listening_socket = None
        self.sock = None
        self.selector = selectors.DefaultSelector()
        self.name = name
        self.running = True
        self.outgoing_buffer = queue.Queue()

        addr = (host, port)

        print("Starting connection to", addr)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.connect_ex(addr)

        print("Connection Established")

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(self.sock, events, data=None)

    def kill_connection(self):
        self.running = False

    def run(self):
        print("\033[94m" + f"entered run on {self.name}" + "\033[0m")
        try:
            while self.running:
                events = self.selector.select(timeout=1)
                for key, mask in events:
                    if mask & selectors.EVENT_READ:
                        self._read(key)
                    if mask & selectors.EVENT_WRITE and not self.outgoing_buffer.empty():
                        self._write(key)
                if not self.selector.get_map():
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.selector.close()

    def _read(self, key):
        print("\033[94m" + f"entered read on {self.name}" + "\033[94m")
        try:
            recv_data = self.sock.recv(1024).decode()
            if recv_data:
                print("\033[94m" + "received", repr(recv_data), "from connection", repr(key.fileobj.getpeername()) + "\033[94m")
                self.process_response(recv_data)
            if not recv_data:
                print("closing connection", repr(key))
                self.selector.unregister(self.sock)
                self.sock.close()
        except:
            self.receiveAudio()

    def _write(self, key):
        print("\033[94m" + f"entered write on {self.name}" + "\033[0m")
        try:
            message = self.outgoing_buffer.get_nowait()
        except queue.Empty:
            message = None
        if message:
            sent = self.sock.send(message.encode())

    def process_response(self, data):
        if data == "ACCEPT":
            self.receiveAudio()

    def postMessage(self, message):
        """Function post message on server"""
        self.outgoing_buffer.put(message)

    def receiveAudio(self):
        """Function retrive audio from server"""

        format = pyaudio.get_format_from_width(2)
        channels = 2
        rate = 11025
        chunk = 4096
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=format,
            channels=channels,
            rate=rate,
            output=True,
            frames_per_buffer=chunk
        )

        header_size = struct.calcsize("I")
        data = b""

        while True:
            try:
                while len(data) < header_size:
                    packet = self.sock.recv(4096)

                    if not packet:
                        break

                    data += packet

                data = data[header_size:]
                msg_size = struct.unpack("I", data[:header_size])[0]

                while len(data) < msg_size:
                    data += self.sock.recv(4096)
                    stream.write(data[:msg_size])
                    data = data[msg_size:]
            except:
                break