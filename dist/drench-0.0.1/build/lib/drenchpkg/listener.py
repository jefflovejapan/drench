import socket
from abc import abstractmethod, ABCMeta


class Listener(object):

    __metaclass__ = ABCMeta

    def __init__(self, address='127.0.0.1', port=7000):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((address, port))
        # TODO -- Do I want to keep this? Or is this a debugging thing?
        self.sock.listen(5)
        print 'listening on {}:{}'.format(address, port)

    @abstractmethod
    def read(self):
        pass

    def fileno(self):
        return self.sock.fileno()

    def write(self):
        pass
