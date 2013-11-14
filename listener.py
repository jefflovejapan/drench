import socket


class Listener(object):
    def __init__(self, address='127.0.0.1', port=7000):
        self.sock = socket.socket()
        self.sock.bind((address, port))
        # TODO -- Do I want to keep this? Or is this a debugging thing?
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.listen(5)
        print 'listening on {}:{}'.format(address, port)

    def read(self):
        return self.sock.accept()

    def fileno(self):
        return self.sock.fileno()
