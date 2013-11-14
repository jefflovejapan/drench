from collections import defaultdict
import socket
import select
from collections import namedtuple


select_response = namedtuple('select_response',
                             'readable writable exceptional')


class Reactor(object):
    def __init__(self):
        self.subscribed = defaultdict(list)
        self.sock = socket.socket()

        # Tells OS we want to use this socket again
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock.bind(('127.0.0.1', 7005))

        # Adding server socket to select_list to check for new connections
        # in same call to select inside event loop
        self.select_list = [self.sock]
        self.sock.listen(5)
        print 'Listening on 127.0.0.1:7005'

    def subscribe(self, callback, event):
        self.subscribed[event].append(callback)  # Add our callbacks here

    def trigger(self, event):
        for callback in self.subscribed[event]:  # They get executed when
            callback()                           # their trigger(event)
                                                 # happens
        self.subscribed[event] = []              # Zero everything out

    def event_loop(self):
        while 1:
            doable_lists = select_response(*select.select(self.select_list,
                                                          [], [], 1))

            for i in doable_lists.readable:  # Doesn't require if test
                if i == self.sock:
                    # TODO -- expand this into creating new peers
                    newsocket, addr = self.sock.accept()
                    self.select_list.append(newsocket)
                else:
                    i.read()

                wclos = i.write
                self.subscribed['write'].append(wclos)
                cclos = i.cleanup
                self.subscribed['cleanup'].append(cclos)

            self.trigger('logic')
            self.trigger('write')
            self.trigger('cleanup')


def main():
    reactor = Reactor()
    reactor.event_loop()

if __name__ == '__main__':
    main()
