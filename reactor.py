from collections import defaultdict
import socket
import select
import time
import pudb


class Reactor(object):
    def __init__(self):
        self.subscribed = defaultdict(list)
        self.sock = socket.socket()
        self.sock.bind(('127.0.0.1', 7005))
        self.read_list = []

    def subscribe(self, callback, event):
        self.subscribed[event].append(callback)  # Add our callbacks here

    def trigger(self, event):
        for callback in self.subscribed[event]:  # They get executed when
            callback()                           # their trigger(event)
                                                 # happens

    def read(self, sock):
        def read_clos():
            f = sock.recv(100)
            print "Here's what we received: {}".format(f)
        return read_clos

    def event_loop(self):
        while 1:
            self.sock.listen(5)
            newsocket, addr = self.sock.accept()     # Get a client, any client
            newsocket.setblocking(False)
            self.read_list.append(newsocket)         # Add to read_list
            rrlist, _, _ = select.select(self.read_list, [], [])
            if rrlist:
                for i in rrlist:                # ready to read
                    clos = self.read(i)
                    self.subscribed['read'].append(clos)
            time.sleep(2)
            for func in self.subscribed['read']:
                func()


def main():
    reactor = Reactor()

    reactor.event_loop()

if __name__ == '__main__':
    main()
