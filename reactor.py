from collections import defaultdict
import socket
import select
import time
import pudb


# TODO - add server socket to select call (if self.sock)
class Reactor(object):
    def __init__(self):
        self.subscribed = defaultdict(list)
        self.sock = socket.socket()

        # Tells OS we want to use this socket again
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock.bind(('127.0.0.1', 7005))

        # Adding server socket to read_list to check for new connections
        # in same call to select inside event loop
        self.read_list = [self.sock]

        self.sock.listen(5)
        print 'Listening on 127.0.0.1:7005'

    def subscribe(self, callback, event):
        self.subscribed[event].append(callback)  # Add our callbacks here

    def trigger(self, event):
        for callback in self.subscribed[event]:  # They get executed when
            callback()                           # their trigger(event)
                                                 # happens

    def read(self, sock):
        def read_clos():
            print sock.getsockname()
            f = sock.recv(100)
            print ("Here's what we received at time {} from {}"
                   ": {}").format(time.clock(), sock.fileno(), f)
            self.subscribed['read'].remove(read_clos)
            print self.subscribed['read']
        read_clos.__name__ = "closure that reads on {}".format(repr(sock))
        return read_clos

    def event_loop(self):
        while 1:
            rrlist, _, _ = select.select(self.read_list, [], [])
            for i in rrlist:  # Doesn't require if test
                if i == self.sock:

                    # Get each client waiting to connect
                    newsocket, addr = self.sock.accept()
                    self.read_list.append(newsocket)
                else:
                    clos = self.read(i)
                    self.subscribed['read'].append(clos)
            self.trigger('read')

        '''
        You only want to call the callbacks if the events actually happened.
        Manage everything by timing / coordinating the callbacks.
        '''


def main():
    reactor = Reactor()
    reactor.event_loop()

if __name__ == '__main__':
    main()
